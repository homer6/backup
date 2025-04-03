# S3 Backup Tool

A Python utility for backing up data from one S3 bucket to another, using a local staging directory.

## Features

- Back up specific folders (prefixes) from one S3 bucket to another
- Transfer between different AWS accounts/profiles
- Local staging allows for verification of data before upload
- Optional cleanup of staging directories
- Configurable source and destination buckets

## Installation

No special installation required - just clone the repository and ensure you have the following:

- Python 3.6+
- AWS CLI v2
- Properly configured AWS credentials

## Usage

### Performing Backups

```
python backup_s3.py <folder_name> [options]
```

#### Arguments

- `folder_name`: The specific folder (prefix) within the source bucket to back up

#### Options

- `--cleanup`: Remove local staging directory after successful upload
- `--use-delete`: Use the `--delete` flag with `aws s3 sync` during download (removes local files not in source)
- `--confirm`: Prompt for confirmation before each operation step
- `--source-profile`: AWS profile for source bucket (default: uses default profile)
- `--dest-profile`: AWS profile for destination bucket (default: "prod-3")
- `--source-bucket`: Source S3 bucket name (default: "studies-db-prod")
- `--dest-bucket`: Destination S3 bucket name (default: "newatlantis-science")

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

Back up a folder with confirmation at each step:

```bash
python backup_s3.py my-folder --confirm
```

Back up a folder using custom profiles and buckets (confirm at each step):

```bash
python backup_s3.py SampleData --source-profile dev --dest-profile prod --source-bucket source-data --dest-bucket dest-data --confirm
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
- `clear_staging.py`: Script for managing staging directories