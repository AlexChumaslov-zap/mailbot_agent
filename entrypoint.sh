#!/bin/bash
# Write the service account JSON from the environment variable to a file.
# ECS injects GOOGLE_SERVICE_ACCOUNT_JSON from Secrets Manager.
if [ -n "$GOOGLE_SERVICE_ACCOUNT_JSON" ]; then
    echo "$GOOGLE_SERVICE_ACCOUNT_JSON" > /app/service_account.json
fi

# Run the command passed to the container (default: uvicorn)
exec "$@"
