#!/bin/bash

# Configuration
REMOTE_HOST="ec2-user@18.217.16.197"
CONTAINER_NAME="0e33cf97cd05"
CONTAINER_PATH="/home/metr/app/src/logs/2025-06-27T21-11-58+00-00_free-response_49UUvqTbfxKYfeMgAX6LSv.eval"
LOCAL_PATH="./downloaded_log.eval"

echo "Downloading log file from container..."
echo "Remote host: $REMOTE_HOST"
echo "Container: $CONTAINER_NAME"
echo "Container path: $CONTAINER_PATH"
echo "Local path: $LOCAL_PATH"
echo ""

# Copy file from container to local machine
ssh $REMOTE_HOST "docker cp $CONTAINER_NAME:$CONTAINER_PATH /tmp/log_file.eval"

if [ $? -eq 0 ]; then
    echo "✓ File copied from container to remote host"

    # Copy file from remote host to local machine
    scp $REMOTE_HOST:/tmp/log_file.eval $LOCAL_PATH

    if [ $? -eq 0 ]; then
        echo "✓ File downloaded successfully to $LOCAL_PATH"

        # Clean up temporary file on remote host
        ssh $REMOTE_HOST "rm /tmp/log_file.eval"
        echo "✓ Cleaned up temporary file on remote host"

        # Show file info
        echo ""
        echo "File downloaded successfully!"
        echo "Size: $(ls -lh $LOCAL_PATH | awk '{print $5}')"
        echo "Location: $(pwd)/$LOCAL_PATH"
    else
        echo "✗ Failed to download file from remote host"
        exit 1
    fi
else
    echo "✗ Failed to copy file from container"
    exit 1
fi
