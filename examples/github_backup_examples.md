# GitHub Backup Examples

This document provides examples of common backup scenarios using the `backup_github.py` script.

## Basic Organization Backups

### Example 1: Backing up an entire organization
```bash
python backup_github.py companyname
```
This command backs up all repositories in the "companyname" organization, creating DAR archives and uploading to S3 bucket "companyname-github-backups" by default.

### Example 2: Backing up an organization with a specific profile
```bash
python backup_github.py engineering-team --dest-profile prod
```
This backs up all repositories in the "engineering-team" organization and uses the "prod" AWS profile for destination.

## Feature Control

### Example 3: Backup without creating archives
```bash
python backup_github.py dev-team --no-archives
```
This clones repositories in the "dev-team" organization without creating DAR archives, but still uploads to S3.

### Example 4: Backup with only local archives (no S3 upload)
```bash
python backup_github.py product-team --no-s3-upload
```
This creates DAR archives for the "product-team" organization but doesn't upload them to S3.

### Example 5: Clone-only backup (no archives, no S3)
```bash
python backup_github.py research-team --no-archives --no-s3-upload
```
This only clones repositories without creating archives or uploading to S3.

## Destination Options

### Example 6: Backup to a specific S3 bucket
```bash
python backup_github.py engineering-team --dest-bucket custom-backup-bucket
```
This backs up all "engineering-team" repositories to the "custom-backup-bucket" S3 bucket instead of the default "engineering-team-github-backups".

### Example 7: Using a custom local path
```bash
python backup_github.py data-team --local-path /mnt/large-volume/github-backups
```
This uses a custom local path for temporary storage during backup.

## Advanced Usage

### Example 8: Including additional repository data
```bash
python backup_github.py design-team --include-wikis --include-lfs
```
This backs up all repositories in the "design-team" organization including wiki pages and LFS objects.

### Example 9: Complete backup with all options
```bash
python backup_github.py company-tools --dest-profile prod --dest-bucket archive-bucket --include-forks --include-wikis --include-lfs --cleanup --local-path /mnt/data/backups
```
This complex example:
- Backs up from "company-tools" organization
- Uses "prod" AWS profile
- Stores backups in "archive-bucket" (overriding default)
- Includes forked repositories
- Includes wiki pages
- Includes LFS objects
- Cleans up temporary files
- Uses custom local path for temporary storage

### Example 10: Advanced archive configuration
```bash
python backup_github.py analytics-team --volume-size 500M --storage-class STANDARD_IA
```
This creates archives with 500MB volume size and uses STANDARD_IA storage class in S3.

## Configuration Options

- `org_name`: GitHub organization name (required, positional argument)
- `--dest-profile`: AWS profile for S3 upload (optional, default: uses default profile)
- `--dest-bucket`: Destination S3 bucket name (optional, default: <org-name>-github-backups)
- `--dest-s3-path`: Destination path within the bucket (optional, default: github_backups/<org_name>)
- `--include-forks`: Include forked repositories in the backup (optional, default: false)
- `--include-wikis`: Download wiki pages for each repository (optional, default: false)
- `--include-lfs`: Include Git LFS objects in the clones (optional, default: false)
- `--no-archives`: Skip creating DAR archives (optional, default: false)
- `--no-s3-upload`: Skip uploading to S3 (optional, default: false)
- `--cleanup`: Remove temporary local files after backup (optional, default: false)
- `--local-path`: Local path for temporary storage (optional, default: ~/github_backup_staging)

## Automated Regular Backups

You can set up a cron job to automatically back up repositories on a schedule:

```bash
# Example crontab entry for daily backups at 2 AM
0 2 * * * /usr/bin/python /path/to/backup_github.py company-name --dest-profile prod --cleanup --local-path /mnt/data/backups >> /var/log/github-backup.log 2>&1
```

This will run a daily backup of the "company-name" organization.

### Example 11: Backing up multiple organizations
```bash
#!/bin/bash

# Define common parameters
DEST_PROFILE="prod"
LOCAL_PATH="/mnt/data/github-backups"

# Back up repositories from different teams
# Each organization will use its own automatically named S3 bucket
python backup_github.py company-team-a --dest-profile $DEST_PROFILE --cleanup --local-path $LOCAL_PATH
python backup_github.py company-team-b --dest-profile $DEST_PROFILE --cleanup --local-path $LOCAL_PATH
python backup_github.py company-team-c --dest-profile $DEST_PROFILE --cleanup --local-path $LOCAL_PATH

# Custom bucket example
python backup_github.py special-project --dest-profile $DEST_PROFILE --dest-bucket custom-archive-bucket --cleanup --local-path $LOCAL_PATH
```

This script demonstrates backing up repositories from different organizations with various configurations.