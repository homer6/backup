# Resumable Backup Examples

This document provides examples of using the resumable backup features to handle large backups that may be interrupted.

## Basic Resumable Backups

### Example 1: Starting a new backup with checkpoint support
```bash
python backup_s3.py LargeDataset --dest-profile prod --source-bucket company-raw-data-db --dest-bucket company-archive --cleanup --base-local-path /mnt/data/scratch
```
When this backup runs, it automatically creates checkpoint files that track progress.

### Example 2: Resuming an interrupted backup
```bash
# Same command as original backup
python backup_s3.py LargeDataset --dest-profile prod --source-bucket company-raw-data-db --dest-bucket company-archive --cleanup --base-local-path /mnt/data/scratch
```
If the backup was previously interrupted, it will automatically detect checkpoint files and resume from where it left off.

## Advanced Checkpoint Management

### Example 3: Specifying custom checkpoint directory
```bash
python backup_s3.py LargeDataset --dest-profile prod --source-bucket company-raw-data-db --dest-bucket company-archive --cleanup --base-local-path /mnt/data/scratch --checkpoint-dir /mnt/data/persistent-checkpoints
```
This stores checkpoint files in a different directory than the default, which may be useful if your local scratch space is volatile.

### Example 4: Forcing a restart by ignoring checkpoints
```bash
python backup_s3.py LargeDataset --dest-profile prod --source-bucket company-raw-data-db --dest-bucket company-archive --cleanup --base-local-path /mnt/data/scratch --ignore-checkpoints
```
This forces the backup to start from the beginning, ignoring any existing checkpoint files.

## Handling Very Large Datasets

### Example 5: Backing up a multi-terabyte dataset with checkpoints
```bash
python backup_s3.py DataWarehouse/2023 --dest-profile prod --source-bucket company-data-warehouse --dest-bucket company-archive --cleanup --base-local-path /mnt/large-volume/scratch --checkpoint-interval 100
```
This adjusts the checkpoint interval to create checkpoints more frequently (every 100 files instead of the default).

### Example 6: Multi-stage backup of extremely large dataset
```bash
# Stage 1: Back up part 1 of dataset
python backup_s3.py BigProject/2023/Q1 --dest-profile prod --source-bucket company-raw-data-db --dest-bucket company-archive --cleanup --base-local-path /mnt/data/scratch

# Stage 2: Back up part 2 of dataset
python backup_s3.py BigProject/2023/Q2 --dest-profile prod --source-bucket company-raw-data-db --dest-bucket company-archive --cleanup --base-local-path /mnt/data/scratch

# Stage 3: Back up part 3 of dataset
python backup_s3.py BigProject/2023/Q3 --dest-profile prod --source-bucket company-raw-data-db --dest-bucket company-archive --cleanup --base-local-path /mnt/data/scratch

# Stage 4: Back up part 4 of dataset
python backup_s3.py BigProject/2023/Q4 --dest-profile prod --source-bucket company-raw-data-db --dest-bucket company-archive --cleanup --base-local-path /mnt/data/scratch
```
For extremely large datasets, you can break the backup into logical parts that each use their own checkpoint files. This example shows backing up quarterly data folders within a nested folder structure.

## Checkpoint File Management

### Example 7: Checkpoint cleanup script
```bash
#!/bin/bash
# cleanup_old_checkpoints.sh

# Set checkpoint directory
CHECKPOINT_DIR="/mnt/data/scratch/checkpoints"

# Find and delete checkpoint files older than 30 days
find $CHECKPOINT_DIR -name "*.checkpoint" -type f -mtime +30 -exec rm {} \;

echo "Removed checkpoint files older than 30 days"
```
This script helps manage checkpoint files by removing old ones that are no longer needed.

## Monitoring Backup Progress

### Example 8: Monitoring script for long-running backups
```bash
#!/bin/bash
# monitor_backup_progress.sh

# Set checkpoint directory
CHECKPOINT_DIR="/mnt/data/scratch/checkpoints"
BACKUP_NAME="LargeDataset"

# Get the latest checkpoint file
LATEST_CHECKPOINT=$(ls -t $CHECKPOINT_DIR/${BACKUP_NAME}*.checkpoint 2>/dev/null | head -1)

if [ -z "$LATEST_CHECKPOINT" ]; then
    echo "No checkpoint file found for $BACKUP_NAME"
    exit 1
fi

# Parse checkpoint file to get progress
TOTAL_FILES=$(grep "total_files" $LATEST_CHECKPOINT | cut -d ":" -f 2 | tr -d " ,")
PROCESSED_FILES=$(grep "processed_files" $LATEST_CHECKPOINT | cut -d ":" -f 2 | tr -d " ,")

if [ -z "$TOTAL_FILES" ] || [ -z "$PROCESSED_FILES" ]; then
    echo "Could not parse checkpoint file"
    exit 1
fi

# Calculate and display progress
PERCENT=$((PROCESSED_FILES * 100 / TOTAL_FILES))
echo "Backup progress for $BACKUP_NAME: $PROCESSED_FILES/$TOTAL_FILES files ($PERCENT%)"
```
This script reads the latest checkpoint file to show backup progress.

## Error Recovery

### Example 9: Handling failed transfers
```bash
python backup_s3.py Reports/Monthly --dest-profile prod --source-bucket company-raw-data-db --dest-bucket company-archive --cleanup --base-local-path /mnt/data/scratch --retry-count 5
```
This increases the number of retry attempts for failed transfers.

### Example 10: Manual checkpoint adjustment
```bash
# Edit the checkpoint file to skip problematic files
sed -i 's/"Reports\/Monthly\/problem_file.dat": false/"Reports\/Monthly\/problem_file.dat": true/' /mnt/data/scratch/checkpoints/company-raw-data-db_Reports_Monthly.checkpoint

# Resume the backup
python backup_s3.py Reports/Monthly --dest-profile prod --source-bucket company-raw-data-db --dest-bucket company-archive --cleanup --base-local-path /mnt/data/scratch
```
This manually edits the checkpoint file to mark a problematic file as processed, then resumes the backup. Note how the checkpoint filename encodes the nested folder structure with underscores.

## Performance Considerations

- Store checkpoint files on fast, reliable storage
- Set appropriate checkpoint intervals based on file sizes
- Consider network and storage performance when planning large backups
- Use separate checkpoint directories for concurrent backups