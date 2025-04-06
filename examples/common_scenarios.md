# Common Backup Scenarios

This document outlines common backup scenarios and how to address them using the backup tools.

## Routine Database Backups

### Scenario: Regular Backup of Critical Research Data

**Challenge**: You need to ensure that critical research data is backed up regularly.

**Solution**:
```bash
# Create a dedicated backup script
#!/bin/bash
# critical_data_backup.sh

# Set up logging
LOG_FILE="/var/log/critical-backup-$(date +%Y-%m-%d).log"
exec > >(tee -a $LOG_FILE) 2>&1

echo "Starting critical data backup at $(date)"

# Back up primary project data with nested folder structure
python /path/to/backup_s3.py Projects/TeamA/Current --dest-profile prod --source-bucket company-data-db --dest-bucket secure-archive --cleanup --base-local-path /mnt/data/scratch
python /path/to/backup_s3.py Projects/TeamB/Current --dest-profile prod --source-bucket company-data-db --dest-bucket secure-archive --cleanup --base-local-path /mnt/data/scratch
python /path/to/backup_s3.py Shared/Reports/Monthly --dest-profile prod --source-bucket company-data-db --dest-bucket secure-archive --cleanup --base-local-path /mnt/data/scratch

echo "Backup completed at $(date)"
```

**Setup**:
1. Save this script as `critical_data_backup.sh`
2. Make it executable: `chmod +x critical_data_backup.sh`
3. Set up a daily cron job: `0 1 * * * /path/to/critical_data_backup.sh`

## Large Dataset Management

### Scenario: Backing Up Multi-Terabyte Datasets

**Challenge**: You need to back up extremely large datasets that may take days to complete.

**Solution**:
```bash
# Use checkpointing for resumable backups with nested folder structure
python backup_s3.py DataWarehouse/2023 --dest-profile prod --source-bucket company-data-warehouse --dest-bucket long-term-archive --cleanup --base-local-path /mnt/large-storage/scratch --checkpoint-interval 50
```

**Process**:
1. Start the backup in a screen or tmux session to prevent interruptions if your connection drops
2. The backup will create checkpoint files every 50 files
3. If interrupted, simply run the same command again to resume

## Organization-Wide Backups

### Scenario: Complete Backup of GitHub Organization Code

**Challenge**: You need to ensure all repositories in your organization and team subgroups are backed up.

**Solution**:
```bash
# Create a script that backs up all repositories including nested team structure
python backup_github.py company/product-team --dest-profile prod --dest-bucket code-archives --cleanup --base-local-path /mnt/data/github-backups
python backup_github.py company/engineering-team --dest-profile prod --dest-bucket code-archives --cleanup --base-local-path /mnt/data/github-backups
python backup_github.py company/platform-team/frontend --dest-profile prod --dest-bucket code-archives --cleanup --base-local-path /mnt/data/github-backups
python backup_github.py company/platform-team/backend --dest-profile prod --dest-bucket code-archives --cleanup --base-local-path /mnt/data/github-backups
```

**Benefits**:
- All repositories are backed up automatically
- New repositories are included in future backups without script changes
- Historical versions are preserved

## Disaster Recovery Planning

### Scenario: Preparing for Disaster Recovery

**Challenge**: You need to establish a comprehensive backup system for disaster recovery.

**Solution**:
```bash
# Master backup script
#!/bin/bash
# disaster_recovery_backup.sh

# Set parameters
DEST_PROFILE="dr-backup"
DEST_BUCKET="disaster-recovery-archives"
LOCAL_PATH="/mnt/dr-storage/scratch"
LOG_FILE="/var/log/dr-backup-$(date +%Y-%m-%d).log"

# Set up logging
exec > >(tee -a $LOG_FILE) 2>&1

echo "Starting disaster recovery backup at $(date)"

# Back up critical S3 buckets with nested folder structure
echo "Backing up primary project data..."
python /path/to/backup_s3.py Projects/TeamA/Current --dest-profile $DEST_PROFILE --source-bucket company-data-db --dest-bucket $DEST_BUCKET --cleanup --base-local-path $LOCAL_PATH
python /path/to/backup_s3.py Projects/TeamB/Current --dest-profile $DEST_PROFILE --source-bucket company-data-db --dest-bucket $DEST_BUCKET --cleanup --base-local-path $LOCAL_PATH

echo "Backing up configuration data..."
python /path/to/backup_s3.py Config/Environments/Production --dest-profile $DEST_PROFILE --source-bucket company-config --dest-bucket $DEST_BUCKET --cleanup --base-local-path $LOCAL_PATH
python /path/to/backup_s3.py Config/Environments/Staging --dest-profile $DEST_PROFILE --source-bucket company-config --dest-bucket $DEST_BUCKET --cleanup --base-local-path $LOCAL_PATH

# Back up code repositories with nested team structure
echo "Backing up code repositories..."
python /path/to/backup_github.py company/product-team --dest-profile $DEST_PROFILE --dest-bucket $DEST_BUCKET --cleanup --base-local-path $LOCAL_PATH
python /path/to/backup_github.py company/engineering-team --dest-profile $DEST_PROFILE --dest-bucket $DEST_BUCKET --cleanup --base-local-path $LOCAL_PATH
python /path/to/backup_github.py company/platform-team/frontend --dest-profile $DEST_PROFILE --dest-bucket $DEST_BUCKET --cleanup --base-local-path $LOCAL_PATH
python /path/to/backup_github.py company/platform-team/backend --dest-profile $DEST_PROFILE --dest-bucket $DEST_BUCKET --cleanup --base-local-path $LOCAL_PATH

echo "Disaster recovery backup completed at $(date)"
```

**Implementation**:
1. Run this script weekly to create comprehensive backups
2. Store the destination bucket in a different AWS region for geographical redundancy
3. Regularly test restoration procedures

## Multi-Environment Backups

### Scenario: Managing Backups Across Development, Staging, and Production

**Challenge**: You need different backup strategies for different environments, each with their own nested folder structures.

**Solution**:
```bash
# Development environment - backed up weekly
python backup_s3.py Projects/TeamA/Dev --dest-profile backup --source-bucket company-dev-data --dest-bucket env-backups --cleanup --base-local-path /mnt/backup/scratch
python backup_s3.py Projects/TeamB/Dev --dest-profile backup --source-bucket company-dev-data --dest-bucket env-backups --cleanup --base-local-path /mnt/backup/scratch

# Staging environment - backed up daily
python backup_s3.py Projects/TeamA/Staging --dest-profile backup --source-bucket company-staging-data --dest-bucket env-backups --cleanup --base-local-path /mnt/backup/scratch
python backup_s3.py Projects/TeamB/Staging --dest-profile backup --source-bucket company-staging-data --dest-bucket env-backups --cleanup --base-local-path /mnt/backup/scratch

# Production environment - backed up daily with duplicates
python backup_s3.py Projects/TeamA/Production --dest-profile backup-primary --source-bucket company-prod-data --dest-bucket primary-backups --cleanup --base-local-path /mnt/backup/scratch
python backup_s3.py Projects/TeamB/Production --dest-profile backup-primary --source-bucket company-prod-data --dest-bucket primary-backups --cleanup --base-local-path /mnt/backup/scratch

# Secondary backup to different storage for disaster recovery
python backup_s3.py Projects/TeamA/Production --dest-profile backup-secondary --source-bucket company-prod-data --dest-bucket secondary-backups --cleanup --base-local-path /mnt/backup/scratch
python backup_s3.py Projects/TeamB/Production --dest-profile backup-secondary --source-bucket company-prod-data --dest-bucket secondary-backups --cleanup --base-local-path /mnt/backup/scratch
```

**Strategy**:
1. Less critical environments (dev) have less frequent backups
2. Production gets duplicate backups to separate buckets
3. Each environment can be restored independently

## Selective Backups

### Scenario: Backing Up Only Recent or Changed Files

**Challenge**: You want to back up only files that have changed or were recently added.

**Solution**:
```bash
# Use AWS CLI to identify recent files, then back up specific folders
#!/bin/bash
# recent_changes_backup.sh

# Find recent changes (last 7 days)
aws s3 ls s3://yourbucket/ --recursive | grep $(date -d "7 days ago" +%Y-%m-%d) | awk '{print $4}' | cut -d/ -f1 | sort | uniq > recent_folders.txt

# Back up each folder with recent changes
while read folder; do
  echo "Backing up folder with recent changes: $folder"
  python backup_s3.py $folder --dest-profile prod --source-bucket yourbucket --dest-bucket backup-bucket --cleanup --base-local-path /mnt/data/scratch
done < recent_folders.txt
```

**Implementation**:
1. This script identifies folders with recently modified files
2. Only those folders are backed up, saving time and resources

## Backup Verification

### Scenario: Verifying Backup Integrity

**Challenge**: You need to verify that backups are complete and valid.

**Solution**:
```bash
# Verification script
#!/bin/bash
# verify_backups.sh

BACKUP_BUCKET="your-backup-bucket"
SOURCE_BUCKET="your-source-bucket"
FOLDER="your-folder"

# Get file counts
SOURCE_COUNT=$(aws s3 ls s3://$SOURCE_BUCKET/$FOLDER/ --recursive | wc -l)
BACKUP_COUNT=$(aws s3 ls s3://$BACKUP_BUCKET/$FOLDER/ --recursive | wc -l)

echo "Source files: $SOURCE_COUNT"
echo "Backup files: $BACKUP_COUNT"

# Check some sample files
echo "Verifying sample files..."
aws s3 ls s3://$SOURCE_BUCKET/$FOLDER/ --recursive | head -10 | awk '{print $4}' | while read file; do
  if aws s3 ls s3://$BACKUP_BUCKET/$file &>/dev/null; then
    echo "✓ $file exists in backup"
  else
    echo "✗ $file missing from backup"
  fi
done
```

**Process**:
1. Run this script after backups complete
2. It compares file counts between source and backup
3. It samples some files to verify they exist in the backup

## Compliance and Retention

### Scenario: Meeting Regulatory Requirements for Data Retention

**Challenge**: You need to maintain backups according to regulatory requirements (e.g., 7 years).

**Solution**:
```bash
# First, set up lifecycle rules on your backup bucket
aws s3api put-bucket-lifecycle-configuration --bucket your-backup-bucket --lifecycle-configuration file://lifecycle.json

# Content of lifecycle.json:
{
  "Rules": [
    {
      "ID": "Keep for 7 years",
      "Status": "Enabled",
      "Prefix": "",
      "Transition": {
        "Days": 90,
        "StorageClass": "GLACIER"
      },
      "Expiration": {
        "Days": 2555
      }
    }
  ]
}

# Then run your backup as normal
python backup_s3.py ComplianceData --dest-profile prod --source-bucket regulated-data --dest-bucket your-backup-bucket --cleanup --base-local-path /mnt/data/scratch
```

**Strategy**:
1. Configure the backup bucket with appropriate lifecycle rules
2. Recent backups stay in standard storage for easy access
3. Older backups transition to Glacier for cost-effective long-term storage
4. Backups are automatically expired after the retention period