# S3 Backup Tool

A Python utility for backing up data from one S3 bucket to another, using a local staging directory with archiving and timestamping.

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
- AWS CLI v2
- DAR (Disk ARchive) utility installed
  - Ubuntu/Debian: `sudo apt install dar`
  - macOS: `brew install dar`
- Properly configured AWS credentials

## Usage

### Performing Backups

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
- `--checkpoint-file`: Path to checkpoint file to save progress (enables resumable backups)
- `--resume`: Resume a previously interrupted backup using the checkpoint file

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

# Resume a previously interrupted backup
python backup_s3.py my-folder --checkpoint-file ~/backups/checkpoint.json --resume
```

Clear a specific folder's staging directory:

```bash
python clear_staging.py --folder my-folder
```

Clear all staging directories:

```bash
python clear_staging.py --all
```

## Code Structure

- `backup_s3.py`: Main script for executing backups
- `backup_utils/s3_backup.py`: Core S3Backup class with backup functionality
- `backup_utils/checkpoint.py`: Handles checkpoint management for resumable backups
- `clear_staging.py`: Script for managing staging directories

## Backup Process

1. Download files from source S3 bucket to local staging directory
2. Archive the downloaded data into fixed-size volumes using DAR
3. Upload the archives to destination S3 bucket with timestamp and specified storage class
4. Optionally clean up local staging and archive directories

## Resumable Backups

The script supports checkpoint-based resumable backups. This allows you to resume an interrupted backup process without having to restart from the beginning.

When using the `--checkpoint-file` option, the script saves the current state after each major step:
- After download from S3 is complete
- After archive creation is complete
- After upload to destination S3 is complete

If the backup process is interrupted (e.g., due to network issues, system crash, etc.), you can resume from the last successful step by using the `--resume` flag along with the same checkpoint file.

Example workflow:
1. Start a backup with checkpointing: `python backup_s3.py my-folder --checkpoint-file ~/backups/my-folder-checkpoint.json`
2. If the process is interrupted, resume with: `python backup_s3.py my-folder --checkpoint-file ~/backups/my-folder-checkpoint.json --resume`

The script will automatically skip completed steps and continue from where it left off.