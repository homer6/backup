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

## Usage

```
python backup_s3.py [folder_name] [options]
```

### Arguments

- `folder_name`: (Optional) The specific folder (prefix) within the source bucket to back up. If omitted, the entire bucket will be backed up.

### Options

- `--source-bucket`: Source S3 bucket name (required)
- `--dest-bucket`: Destination S3 bucket name (required)
- `--source-profile`: AWS profile for source bucket (optional, default: uses default profile)
- `--dest-profile`: AWS profile for destination bucket (optional, default: uses default profile)
- `--dest-path`: Destination path within the bucket (optional, default: same as source bucket name)
- `--base-local-path`: Base directory on local machine for temporary downloads (optional, default: ~/s3_backup_staging)
- `--storage-class`: Storage class for S3 objects (optional, default: "DEEP_ARCHIVE", options: "STANDARD", "REDUCED_REDUNDANCY", "STANDARD_IA", "ONEZONE_IA", "INTELLIGENT_TIERING", "GLACIER", "DEEP_ARCHIVE", "GLACIER_IR", "EXPRESS_ONEZONE")
- `--cleanup`: Remove local staging and archive directories after successful upload (optional, default: false)
- `--use-delete`: Use the `--delete` flag with `aws s3 sync` during download (optional, removes local files not in source)
- `--confirm`: Prompt for confirmation before each operation step (optional)
- `--volume-size`: Size limit for each archive volume (optional, default: 1G)
- `--checkpoint-file`: Path to checkpoint file to save progress (optional, default: auto-generated based on inputs)
- `--no-resume`: Don't resume from previous checkpoint, even if one exists (optional, default: false)

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

# Backups now automatically resume if interrupted
python backup_s3.py my-folder

# To force starting a fresh backup without resuming
python backup_s3.py my-folder --no-resume

# Specify a custom checkpoint file if needed
python backup_s3.py my-folder --checkpoint-file ~/backups/checkpoint.json
```

## Process

1. Download files from source S3 bucket to local staging directory
2. Archive the downloaded data into fixed-size volumes using DAR
3. Upload the archives to destination S3 bucket with timestamp and specified storage class
4. Optionally clean up local staging and archive directories