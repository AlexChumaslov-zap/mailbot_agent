"""IMAP IDLE listener that monitors Gmail for [RFI] emails and stores them."""

import os
import logging
import time
import email as email_lib
from email.header import decode_header
from email.utils import parsedate_to_datetime
from typing import List, Optional

import imapclient
from dotenv import load_dotenv

from app.models.email_model import RfiEmailCreate, AttachmentCreate
from app.services.database import save_rfi_email, rfi_exists
from app.services.s3_service import upload_bytes

load_dotenv()

logger = logging.getLogger(__name__)

IMAP_SERVER = os.getenv("IMAP_SERVER", "imap.gmail.com")
IMAP_EMAIL = os.getenv("IMAP_EMAIL", "")
IMAP_PASSWORD = os.getenv("IMAP_PASSWORD", "")
S3_ATTACHMENT_PREFIX = os.getenv("S3_ATTACHMENT_PREFIX", "rfi-attachments")

RFI_TAG = "[RFI]"
IDLE_TIMEOUT = 300  # seconds – re-issue IDLE every 5 min to stay alive


def _decode_header_value(raw: Optional[str]) -> str:
    """Decode an RFC-2047 encoded header into a plain string."""
    if raw is None:
        return ""
    parts = decode_header(raw)
    decoded = []
    for fragment, charset in parts:
        if isinstance(fragment, bytes):
            decoded.append(fragment.decode(charset or "utf-8", errors="replace"))
        else:
            decoded.append(fragment)
    return "".join(decoded)


def _extract_attachments(msg: email_lib.message.Message, rfi_subject: str) -> List[AttachmentCreate]:
    """Walk a MIME message and upload attachments to S3."""
    attachments: List[AttachmentCreate] = []
    for part in msg.walk():
        disposition = part.get_content_disposition()
        if disposition != "attachment":
            continue

        filename = part.get_filename()
        if filename is None:
            continue
        filename = _decode_header_value(filename)

        payload = part.get_payload(decode=True)
        if payload is None:
            continue

        content_type = part.get_content_type() or "application/octet-stream"
        file_size = len(payload)

        # Build a unique S3 key:  rfi-attachments/<sanitised_subject>/<filename>
        safe_subject = "".join(c if c.isalnum() or c in " -_" else "_" for c in rfi_subject)[:80]
        s3_key = f"{S3_ATTACHMENT_PREFIX}/{safe_subject}/{filename}"

        try:
            upload_bytes(payload, s3_key, content_type)
            logger.info("Uploaded attachment %s (%d bytes) → s3://%s", filename, file_size, s3_key)
        except Exception:
            logger.exception("Failed to upload attachment %s to S3", filename)
            s3_key = None  # record the attachment anyway, without S3 link

        attachments.append(AttachmentCreate(
            filename=filename,
            content_type=content_type,
            file_size=file_size,
            s3_key=s3_key,
        ))

    return attachments


def _process_message(client: imapclient.IMAPClient, uid: int) -> bool:
    """Fetch a single message by UID, check for [RFI], store if matched.

    Returns True if the message was an RFI and was saved.
    """
    # Fetch headers first to check subject and dedup before downloading full body
    raw_headers = client.fetch([uid], ["BODY[HEADER]"])
    raw_hdr = raw_headers.get(uid)
    if raw_hdr is None:
        return False

    header_msg = email_lib.message_from_bytes(raw_hdr[b"BODY[HEADER]"])

    subject = _decode_header_value(header_msg["Subject"])
    if RFI_TAG not in subject:
        return False

    message_id = header_msg["Message-ID"] or ""

    # Skip if already stored — avoids re-downloading body and re-uploading attachments
    if message_id and rfi_exists(message_id):
        logger.info("Skipping duplicate RFI email message_id=%s", message_id)
        client.set_flags([uid], [b"\\Seen"], silent=True)
        return False

    # Now fetch the full message for attachments
    raw_messages = client.fetch([uid], ["RFC822"])
    raw = raw_messages.get(uid)
    if raw is None:
        return False

    msg = email_lib.message_from_bytes(raw[b"RFC822"])
    sender = _decode_header_value(msg["From"])

    try:
        email_date = parsedate_to_datetime(msg["Date"]).strftime("%Y-%m-%d %H:%M:%S UTC")
    except Exception:
        email_date = ""

    attachments = _extract_attachments(msg, subject)

    try:
        saved = save_rfi_email(RfiEmailCreate(
            message_id=message_id,
            sender=sender,
            subject=subject,
            body=None,
            email_date=email_date,
            attachments=attachments,
        ))
        logger.info("Saved RFI email id=%s subject='%s' with %d attachments",
                     saved.id, subject, len(attachments))
    except Exception:
        logger.exception("Failed to save RFI email subject='%s'", subject)
        return False

    # Mark as read (add \Seen flag)
    client.set_flags([uid], [b"\\Seen"], silent=True)
    return True


def _process_unseen(client: imapclient.IMAPClient) -> int:
    """Search for all UNSEEN messages and process any [RFI] ones.

    Returns the number of RFI emails saved.
    """
    uids = client.search(["UNSEEN"])
    if not uids:
        return 0

    logger.info("Found %d unseen message(s), scanning for [RFI]…", len(uids))
    saved_count = 0
    for uid in uids:
        try:
            if _process_message(client, uid):
                saved_count += 1
        except Exception:
            logger.exception("Error processing UID %s", uid)
    return saved_count


def _connect() -> imapclient.IMAPClient:
    """Create and authenticate an IMAP client."""
    client = imapclient.IMAPClient(IMAP_SERVER, ssl=True)
    client.login(IMAP_EMAIL, IMAP_PASSWORD)
    client.select_folder("INBOX")
    logger.info("Connected to %s as %s", IMAP_SERVER, IMAP_EMAIL)
    return client


def idle_loop() -> None:
    """Long-running loop: connect, process existing unreads, then IDLE for new mail.

    Automatically reconnects on errors.
    """
    while True:
        try:
            client = _connect()

            # On first connect, process any backlog of unseen [RFI] messages
            _process_unseen(client)

            # Enter IDLE loop
            while True:
                client.idle()
                responses = client.idle_check(timeout=IDLE_TIMEOUT)
                client.idle_done()

                # Check if any response signals new mail (EXISTS)
                has_new = any(
                    isinstance(r, tuple) and len(r) >= 2 and r[1] == b"EXISTS"
                    for r in responses
                )
                if has_new:
                    _process_unseen(client)

        except Exception:
            logger.exception("IMAP connection error, reconnecting in 10s…")
            time.sleep(10)
