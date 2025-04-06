# Backup Automation Examples

This document provides examples for automating backups using shell scripts and scheduling tools.

## Scheduled Backups

### Example 1: Daily S3 Backup Script
```bash
#!/bin/bash
# daily_s3_backup.sh - Run daily at midnight via cron

# Define common parameters
DEST_PROFILE="prod"
DEST_BUCKET="company-archive"
LOCAL_PATH="/mnt/data/scratch"

# Log start time
echo "Starting daily backup at $(date)"

# Back up critical databases with nested folder paths
python /path/to/backup_s3.py Projects/TeamA/Current --dest-profile $DEST_PROFILE --source-bucket company-data-db --dest-bucket $DEST_BUCKET --cleanup --base-local-path $LOCAL_PATH
python /path/to/backup_s3.py Projects/TeamB/Current --dest-profile $DEST_PROFILE --source-bucket company-data-db --dest-bucket $DEST_BUCKET --cleanup --base-local-path $LOCAL_PATH
python /path/to/backup_s3.py Shared/Reports --dest-profile $DEST_PROFILE --source-bucket company-data-db --dest-bucket $DEST_BUCKET --cleanup --base-local-path $LOCAL_PATH

# Back up raw data
python /path/to/backup_s3.py --dest-profile $DEST_PROFILE --source-bucket company-raw-data-db --dest-bucket $DEST_BUCKET --cleanup --base-local-path $LOCAL_PATH

echo "Daily backup completed at $(date)"
```

### Example 2: Weekly GitHub Backup Script
```bash
#!/bin/bash
# weekly_github_backup.sh - Run weekly on Sundays via cron

# Define parameters
DEST_PROFILE="prod"
DEST_BUCKET="github-archives"
LOCAL_PATH="/mnt/data/github-backups"

# Log start time
echo "Starting weekly GitHub backup at $(date)"

# Back up primary organizations with nested team structure
python /path/to/backup_github.py company/product-team --dest-profile $DEST_PROFILE --dest-bucket $DEST_BUCKET --cleanup --base-local-path $LOCAL_PATH
python /path/to/backup_github.py company/engineering-team --dest-profile $DEST_PROFILE --dest-bucket $DEST_BUCKET --cleanup --base-local-path $LOCAL_PATH
python /path/to/backup_github.py company/platform-team/frontend --dest-profile $DEST_PROFILE --dest-bucket $DEST_BUCKET --cleanup --base-local-path $LOCAL_PATH
python /path/to/backup_github.py company/platform-team/backend --dest-profile $DEST_PROFILE --dest-bucket $DEST_BUCKET --cleanup --base-local-path $LOCAL_PATH

echo "Weekly GitHub backup completed at $(date)"
```

## Cron Setup Examples

### Example 3: Crontab Entries for Scheduled Backups
```
# Daily S3 backup at midnight
0 0 * * * /path/to/daily_s3_backup.sh >> /var/log/daily-s3-backup.log 2>&1

# Weekly GitHub backup on Sundays at 1 AM
0 1 * * 0 /path/to/weekly_github_backup.sh >> /var/log/weekly-github-backup.log 2>&1

# Monthly full backup on the 1st of each month at 3 AM
0 3 1 * * /path/to/monthly_full_backup.sh >> /var/log/monthly-full-backup.log 2>&1
```

## Comprehensive Backup Solutions

### Example 4: Complete Backup Script with Notifications
```bash
#!/bin/bash
# comprehensive_backup.sh

# Configuration
DEST_PROFILE="prod"
DEST_BUCKET="company-archive"
LOCAL_PATH="/mnt/data/scratch"
NOTIFICATION_EMAIL="admin@example.com"

# Start timestamp
START_TIME=$(date +%s)
echo "Starting comprehensive backup at $(date)"

# Function to send notification
send_notification() {
    local subject="$1"
    local message="$2"
    echo "$message" | mail -s "$subject" $NOTIFICATION_EMAIL
}

# Run backups with error handling
run_backup() {
    local description="$1"
    local command="$2"
    
    echo "Starting backup: $description"
    if eval "$command"; then
        echo "Completed backup: $description"
        return 0
    else
        echo "FAILED backup: $description"
        send_notification "Backup Failed: $description" "The backup command failed with exit code $?"
        return 1
    }
}

# S3 Backups with nested folder structures
run_backup "Projects - Team A" "python /path/to/backup_s3.py Projects/TeamA/Current --dest-profile $DEST_PROFILE --source-bucket company-data-db --dest-bucket $DEST_BUCKET --cleanup --base-local-path $LOCAL_PATH"
run_backup "Projects - Team B" "python /path/to/backup_s3.py Projects/TeamB/Current --dest-profile $DEST_PROFILE --source-bucket company-data-db --dest-bucket $DEST_BUCKET --cleanup --base-local-path $LOCAL_PATH"
run_backup "Projects - Team C" "python /path/to/backup_s3.py Projects/TeamC/Current --dest-profile $DEST_PROFILE --source-bucket company-data-db --dest-bucket $DEST_BUCKET --cleanup --base-local-path $LOCAL_PATH"
run_backup "Reports Database" "python /path/to/backup_s3.py Reports/2024 --dest-profile $DEST_PROFILE --source-bucket company-reports-db --dest-bucket $DEST_BUCKET --cleanup --base-local-path $LOCAL_PATH"

# GitHub Backups with nested team structure
run_backup "Product Team Repos" "python /path/to/backup_github.py company/product-team --dest-profile $DEST_PROFILE --dest-bucket $DEST_BUCKET --cleanup --base-local-path $LOCAL_PATH"
run_backup "Engineering Team Repos" "python /path/to/backup_github.py company/engineering-team --dest-profile $DEST_PROFILE --dest-bucket $DEST_BUCKET --cleanup --base-local-path $LOCAL_PATH"

# Calculate duration
END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))
HOURS=$((DURATION / 3600))
MINUTES=$(( (DURATION % 3600) / 60 ))
SECONDS=$((DURATION % 60))

# Send completion notification
SUMMARY="Comprehensive backup completed in ${HOURS}h ${MINUTES}m ${SECONDS}s"
echo $SUMMARY
send_notification "Backup Completed" "$SUMMARY"
```

## AWS Lambda Triggers

### Example 5: CloudWatch Event to Trigger Backup
```json
{
  "name": "DailyBackupTrigger",
  "description": "Triggers EC2 backup instance daily",
  "scheduleExpression": "cron(0 0 * * ? *)",
  "targets": [
    {
      "id": "StartBackupInstance",
      "arn": "arn:aws:lambda:us-west-2:123456789012:function:StartBackupEC2Instance"
    }
  ]
}
```

This CloudWatch Event rule triggers a Lambda function daily at midnight, which could start an EC2 instance that runs the backup scripts.

## Docker-Based Backup Solution

### Example 6: Docker Container for Portable Backups
```dockerfile
FROM python:3.9-slim

# Install dependencies
RUN apt-get update && apt-get install -y \
    git \
    && rm -rf /var/lib/apt/lists/*

# Set up working directory
WORKDIR /app

# Copy backup scripts
COPY backup_s3.py backup_github.py requirements.txt ./
COPY backup_utils/ ./backup_utils/

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy automation scripts and examples
COPY examples/daily_s3_backup.sh examples/weekly_github_backup.sh ./
COPY examples/nested_folder_backups.sh ./

# Make scripts executable
RUN chmod +x daily_s3_backup.sh weekly_github_backup.sh nested_folder_backups.sh

# Default command
CMD ["bash", "-c", "echo 'Backup container ready. Run specific backup script as needed.'"]
```

The `nested_folder_backups.sh` script demonstrates backing up nested folder structures:

```bash
#!/bin/bash
# nested_folder_backups.sh - Example of backing up nested folders

# Define common parameters
DEST_PROFILE="prod"
DEST_BUCKET="company-archive"
LOCAL_PATH="/mnt/data/scratch"

# Back up nested folder structures from different projects
python /app/backup_s3.py Projects/TeamA/2024Q1 --dest-profile $DEST_PROFILE --source-bucket company-data-db --dest-bucket $DEST_BUCKET --cleanup --base-local-path $LOCAL_PATH
python /app/backup_s3.py Projects/TeamA/2024Q2 --dest-profile $DEST_PROFILE --source-bucket company-data-db --dest-bucket $DEST_BUCKET --cleanup --base-local-path $LOCAL_PATH
python /app/backup_s3.py Projects/TeamB/2024Q1 --dest-profile $DEST_PROFILE --source-bucket company-data-db --dest-bucket $DEST_BUCKET --cleanup --base-local-path $LOCAL_PATH
python /app/backup_s3.py Projects/TeamB/2024Q2 --dest-profile $DEST_PROFILE --source-bucket company-data-db --dest-bucket $DEST_BUCKET --cleanup --base-local-path $LOCAL_PATH
python /app/backup_s3.py References/External/2024 --dest-profile $DEST_PROFILE --source-bucket company-data-db --dest-bucket $DEST_BUCKET --cleanup --base-local-path $LOCAL_PATH
```

This Dockerfile creates a portable backup environment that can be deployed anywhere.

## Security Considerations

- Store AWS credentials securely using IAM roles or environment variables
- Use least-privilege permissions for backup users/roles
- Encrypt backups at rest and in transit
- Regularly rotate access keys
- Monitor backup logs for failures and suspicious activities