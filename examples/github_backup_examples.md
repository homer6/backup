# GitHub Backup Examples

This document provides examples of common backup scenarios using the `backup_github.py` script.

## Basic Organization Backups

### Example 1: Backing up an entire organization
```bash
python backup_github.py companyname
```
This command backs up all repositories in the "companyname" organization.

### Example 2: Backing up an organization with a specific profile
```bash
python backup_github.py engineering-team --dest-profile prod
```
This backs up all repositories in the "engineering-team" organization and uses the "prod" AWS profile for destination.

## Filtered Backups

### Example 3: Backing up with specific filters
```bash
python backup_github.py dev-team --include "service-*" --exclude "*-deprecated"
```
This backs up repositories in the "dev-team" organization that match the pattern "service-*" but excludes any with names ending in "-deprecated".

### Example 4: Backing up specific repositories
```bash
python backup_github.py product-team --repos "core-lib,analysis-tools,web-dashboard"
```
This backs up only the specified repositories from the "product-team" organization.

## Destination Options

### Example 5: Backup to a specific S3 bucket
```bash
python backup_github.py engineering-team --dest-bucket custom-backup-bucket
```
This backs up all "engineering-team" repositories to the "custom-backup-bucket" S3 bucket.

### Example 6: Using a custom local path
```bash
python backup_github.py data-team --base-local-path /mnt/large-volume/github-backups
```
This uses a custom local path for temporary storage during backup.

## Advanced Usage

### Example 7: Complete backup with all options
```bash
python backup_github.py company-tools --dest-profile prod --dest-bucket archive-bucket --include "api-*" --exclude "*-test" --repos "core-service,data-processor" --cleanup --base-local-path /mnt/data/backups
```
This complex example:
- Backs up from "company-tools" organization
- Uses "prod" AWS profile
- Stores backups in "archive-bucket"
- Includes repos matching "api-*"
- Excludes repos ending with "-test"
- Explicitly includes "core-service" and "data-processor" repos
- Cleans up temporary files
- Uses custom local path for temporary storage

## Configuration Options

- `org_name`: GitHub organization name (required, positional argument)
- `--dest-profile`: AWS profile for destination bucket (optional)
- `--dest-bucket`: Destination S3 bucket name (optional)
- `--include`: Pattern for repositories to include (optional)
- `--exclude`: Pattern for repositories to exclude (optional)
- `--repos`: Comma-separated list of specific repositories to backup (optional)
- `--cleanup`: Remove temporary local files after backup (optional)
- `--base-local-path`: Local path for temporary storage (optional)

## Automated Regular Backups

You can set up a cron job to automatically back up repositories on a schedule:

```bash
# Example crontab entry for daily backups at 2 AM
0 2 * * * /usr/bin/python /path/to/backup_github.py company-name --dest-profile prod --cleanup --base-local-path /mnt/data/backups >> /var/log/github-backup.log 2>&1
```

This will run a daily backup of the "company-name" organization.

### Example 8: Backing up multiple nested team organizations
```bash
#!/bin/bash

# Define common parameters
DEST_PROFILE="prod"
DEST_BUCKET="github-archives"
LOCAL_PATH="/mnt/data/github-backups"

# Back up repositories from different teams
python backup_github.py company/team-a --dest-profile $DEST_PROFILE --dest-bucket $DEST_BUCKET --cleanup --base-local-path $LOCAL_PATH
python backup_github.py company/team-b --dest-profile $DEST_PROFILE --dest-bucket $DEST_BUCKET --cleanup --base-local-path $LOCAL_PATH
python backup_github.py company/team-c/frontend --dest-profile $DEST_PROFILE --dest-bucket $DEST_BUCKET --cleanup --base-local-path $LOCAL_PATH
python backup_github.py company/team-c/backend --dest-profile $DEST_PROFILE --dest-bucket $DEST_BUCKET --cleanup --base-local-path $LOCAL_PATH
```

This script demonstrates backing up repositories from organizations with nested team structures.