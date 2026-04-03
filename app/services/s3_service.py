import os
from pathlib import Path
from dotenv import load_dotenv
import boto3

load_dotenv()

S3_BUCKET = os.getenv("S3_BUCKET", "email-collector-assets")
_s3 = boto3.client("s3")


def download_dir(s3_prefix: str, local_dir: str):
    """Download all files from an S3 prefix to a local directory."""
    local = Path(local_dir)
    local.mkdir(parents=True, exist_ok=True)
    paginator = _s3.get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=S3_BUCKET, Prefix=s3_prefix):
        for obj in page.get("Contents", []):
            key = obj["Key"]
            rel = key[len(s3_prefix):].lstrip("/")
            if not rel:
                continue
            dest = local / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            _s3.download_file(S3_BUCKET, key, str(dest))


def upload_file(local_path: str, s3_key: str):
    """Upload a single file to S3."""
    _s3.upload_file(local_path, S3_BUCKET, s3_key)


def download_file(s3_key: str, local_path: str):
    """Download a single file from S3. Silently skips if the file doesn't exist yet."""
    Path(local_path).parent.mkdir(parents=True, exist_ok=True)
    try:
        _s3.download_file(S3_BUCKET, s3_key, local_path)
    except _s3.exceptions.ClientError:
        pass
