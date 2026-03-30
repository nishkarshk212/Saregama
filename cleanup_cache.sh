#!/bin/bash
# Cache cleanup script for Lily Music Bot
# Run this periodically to free up disk space

DOWNLOADS_DIR="/root/Lily-Music-Deploy/downloads"
MAX_AGE_DAYS=7  # Delete files older than 7 days
MAX_SIZE_MB=500  # Keep total size under 500MB

echo "Starting cache cleanup..."

# Create downloads directory if it doesn't exist
mkdir -p "$DOWNLOADS_DIR"

# Delete old files
find "$DOWNLOADS_DIR" -type f -mtime +$MAX_AGE_DAYS -delete
echo "Deleted files older than $MAX_AGE_DAYS days"

# Check total size and delete oldest if over limit
TOTAL_SIZE=$(du -sm "$DOWNLOADS_DIR" | cut -f1)
if [ "$TOTAL_SIZE" -gt "$MAX_SIZE_MB" ]; then
    echo "Total size ($TOTAL_SIZE MB) exceeds limit ($MAX_SIZE_MB MB)"
    echo "Removing oldest files..."
    # Remove oldest files until under limit
    while [ "$TOTAL_SIZE" -gt "$MAX_SIZE_MB" ]; do
        OLDEST=$(ls -t "$DOWNLOADS_DIR" | tail -1)
        if [ -n "$OLDEST" ]; then
            rm -f "$DOWNLOADS_DIR/$OLDEST"
            echo "Removed: $OLDEST"
        else
            break
        fi
        TOTAL_SIZE=$(du -sm "$DOWNLOADS_DIR" | cut -f1)
    done
fi

echo "Cleanup complete!"
echo "Current cache size: $(du -sh "$DOWNLOADS_DIR" | cut -f1)"
