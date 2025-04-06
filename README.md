# Backup Tools

This repository contains utility scripts for backing up data from various sources.

## S3 Backup Tool

A Python utility for backing up data from one S3 bucket to another, using a local staging directory with archiving and timestamping.

## GitHub Backup Tool

A Python utility for backing up all repositories from a GitHub organization, with options to include wikis and LFS objects, create archives, and upload to S3.

## Features

- Back up specific folders (prefixes) or entire buckets from one S3 bucket to another
- Transfer between different AWS accounts/profiles
- Archives data into fixed-size volumes using DAR 
- Uploads archived data to destination S3 bucket with timestamp
- Configurable S3 storage class (STANDARD, GLACIER, DEEP_ARCHIVE, etc.)
- Local staging allows for verification of data before upload
- Optional cleanup of staging directories
- Configurable source and destination buckets

## Installation

No special installation required - just clone the repository and ensure you have the following:

- Python 3.6+
- AWS CLI v2 (required for S3 operations)
- Git CLI (required for GitHub backup)
- DAR (Disk ARchive) utility installed
  - Ubuntu/Debian: `sudo apt install dar`
  - macOS: `brew install dar`
- Properly configured AWS credentials (for S3 operations)
- GitHub personal access token with `repo` scope (for GitHub backup, set as environment variable `GITHUB_TOKEN`)

## Usage

### S3 Backup

```
python backup_s3.py [folder_name] [options]
```

#### Arguments

- `folder_name`: (Optional) The specific folder (prefix) within the source bucket to back up. If omitted, the entire bucket will be backed up.

#### Options

- `--cleanup`: Remove local staging and archive directories after successful upload
- `--use-delete`: Use the `--delete` flag with `aws s3 sync` during download (removes local files not in source)
- `--confirm`: Prompt for confirmation before each operation step
- `--volume-size`: Size limit for each archive volume (default: 1G)
- `--source-profile`: AWS profile for source bucket (default: uses default profile)
- `--dest-profile`: AWS profile for destination bucket (default: "prod-3")
- `--source-bucket`: Source S3 bucket name (default: "studies-db-prod")
- `--dest-bucket`: Destination S3 bucket name (default: "newatlantis-science")
- `--dest-path`: Destination path within the bucket (default: same as source bucket name)
- `--base-local-path`: Base directory on local machine for temporary downloads (default: ~/s3_backup_staging)
- `--storage-class`: Storage class for S3 objects (default: "DEEP_ARCHIVE", options: "STANDARD", "REDUCED_REDUNDANCY", "STANDARD_IA", "ONEZONE_IA", "INTELLIGENT_TIERING", "GLACIER", "DEEP_ARCHIVE", "GLACIER_IR", "EXPRESS_ONEZONE")
- `--checkpoint-file`: Path to checkpoint file to save progress (by default, a file based on inputs will be used)
- `--no-resume`: Don't resume from previous checkpoint, even if one exists

### GitHub Backup

Backup all repositories in a GitHub organization. The GitHub token must be provided through the environment variable `GITHUB_TOKEN`.

```
python backup_github.py <org_name> [options]
```

#### Arguments

- `org_name`: GitHub organization name to backup.

#### Options

- `--local-path`: Base directory on local machine for repository backups (default: ~/github_backup_staging)
- `--include-forks`: Include forked repositories in the backup
- `--include-wikis`: Download wiki pages for each repository
- `--include-lfs`: Include Git LFS objects in the clones
- `--cleanup`: Remove local repositories after successful backup
- `--confirm`: Confirm each step before execution
- `--create-archives`: Create archives of each repository
- `--volume-size`: Size limit for each archive volume (default: 1G)
- `--upload-to-s3`: Upload archives to S3 bucket
- `--s3-profile`: AWS profile for S3 upload
- `--s3-bucket`: Destination S3 bucket name
- `--s3-path`: Destination path within the bucket (default: github_backups/<org_name>)
- `--storage-class`: Storage class for S3 objects (default: "DEEP_ARCHIVE")
- `--checkpoint-file`: Path to checkpoint file to save progress
- `--no-resume`: Don't resume from previous checkpoint, even if one exists

### Clearing Staging Directories

The `clear_staging.py` script allows you to safely delete staging directories when needed:

```
python clear_staging.py [--folder FOLDER | --all] [options]
```

#### Options

- `--folder FOLDER`: Clear a specific folder's staging directory
- `--all`: Clear all staging directories
- `--force`: Skip confirmation prompts
- `--source-profile`: AWS profile for source bucket 
- `--source-bucket`: Source S3 bucket name
- `--staging-path`: Override default staging path

## Examples

### S3 Backup Examples

Back up a folder named "my-folder" with cleanup:

```bash
python backup_s3.py my-folder --cleanup
```

Back up an entire bucket with confirmation at each step:

```bash
python backup_s3.py --source-bucket my-bucket --confirm
```

Back up a folder with confirmation at each step:

```bash
python backup_s3.py my-folder --confirm
```

Back up a folder using custom profiles, buckets, and volume size (confirm at each step):

```bash
python backup_s3.py SampleData --source-profile dev --dest-profile prod --source-bucket source-data --dest-bucket dest-data --dest-path backups/2025 --base-local-path /tmp/s3_staging --volume-size 500M --confirm
```

Back up an entire bucket using a specific storage class:

```bash
python backup_s3.py --source-bucket my-bucket --dest-bucket archive-bucket --storage-class GLACIER --confirm

# Backups now automatically resume if interrupted
python backup_s3.py my-folder

# To force starting a fresh backup without resuming
python backup_s3.py my-folder --no-resume

# Specify a custom checkpoint file if needed
python backup_s3.py my-folder --checkpoint-file ~/backups/checkpoint.json
```

### GitHub Backup Examples

First, set your GitHub token as an environment variable:

```bash
export GITHUB_TOKEN=your_github_personal_access_token
```

Back up all repositories in an organization:

```bash
python backup_github.py my-org-name
```

Back up all repositories including wikis and LFS objects:

```bash
python backup_github.py my-org-name --include-wikis --include-lfs
```

Back up all repositories, create archives, and upload to S3:

```bash
python backup_github.py my-org-name --create-archives --upload-to-s3 --s3-bucket my-backup-bucket
```

Back up all repositories with confirmation at each step:

```bash
python backup_github.py my-org-name --confirm
```

Resume a previously interrupted backup:

```bash
python backup_github.py my-org-name
```

### Other Examples

Clear a specific folder's staging directory:

```bash
python clear_staging.py --folder my-folder
```

Clear all staging directories:

```bash
python clear_staging.py --all
```

## Code Structure

- `backup_s3.py`: Main script for executing S3 backups
- `backup_github.py`: Main script for executing GitHub organization backups
- `backup_utils/s3_backup.py`: Core S3Backup class with S3 backup functionality
- `backup_utils/github_backup.py`: Core GitHubBackup class with GitHub backup functionality
- `backup_utils/checkpoint.py`: Handles checkpoint management for resumable backups
- `clear_staging.py`: Script for managing staging directories

## Backup Processes

### S3 Backup Process

1. Download files from source S3 bucket to local staging directory
2. Archive the downloaded data into fixed-size volumes using DAR
3. Upload the archives to destination S3 bucket with timestamp and specified storage class
4. Optionally clean up local staging and archive directories

### GitHub Backup Process

1. Fetch the list of repositories for the specified organization
2. Clone each repository (with optional wiki and LFS objects)
3. Optionally create archives of each repository using DAR
4. Optionally upload the archives to S3 with timestamp
5. Optionally clean up local repositories and archive directories

## Resumable Backups

Both the S3 and GitHub backup scripts automatically use resumable backups with smart checkpoint file naming. This allows you to resume an interrupted backup process without having to restart from the beginning.

Key features of the automatic checkpointing system:

- Checkpoint files are automatically created based on backup configuration:
  - For S3: based on bucket and folder names, stored in `~/s3_backup_staging/.checkpoints/`
  - For GitHub: based on organization name, stored in `~/github_backup_staging/.checkpoints/`
- The scripts automatically save progress after each major step:
  - For S3 backups:
    - After download from S3 is complete
    - After archive creation is complete
    - After upload to destination S3 is complete
  - For GitHub backups:
    - After fetching repository list
    - After processing each repository
- If a backup is interrupted, simply running the same command again will resume from where it left off
- Use `--no-resume` to start a fresh backup and ignore existing checkpoint
- You can still specify a custom checkpoint file with `--checkpoint-file` if needed

Example workflow:
1. Start a backup: `python backup_s3.py my-folder` or `python backup_github.py my-org-name`
2. If the process is interrupted, run the same command again
3. The script will automatically detect the previous progress and resume from the last completed step