# S3 Backup Examples

This document provides examples of common backup scenarios using the `backup_s3.py` script.

## Basic Database Backups

### Example 1: Backing up a database folder
```bash
python backup_s3.py Analysis --dest-profile prod --source-bucket company-data-db --dest-bucket company-archive --cleanup --base-local-path /mnt/data/scratch
```
This command backs up the "Analysis" folder from the "company-data-db" bucket to the "company-archive" bucket using the "prod" AWS profile. The `--cleanup` flag ensures temporary files are removed after backup completes.

### Example 2: Backing up an entire bucket
```bash
python backup_s3.py --dest-profile prod --source-bucket company-raw-data-db --dest-bucket company-archive --cleanup --base-local-path /mnt/data/scratch
```
When no folder is specified, the entire bucket is backed up.

## Project Backups

### Example 3: Backing up a specific project dataset
```bash
python backup_s3.py ProjectAlpha --dest-profile prod --source-bucket company-projects-db --dest-bucket company-archive --cleanup --base-local-path /mnt/data/scratch
```
This command backs up the "ProjectAlpha" folder which contains a specific project dataset.

### Example 4: Backing up a nested folder structure
```bash
python backup_s3.py Projects/TeamA/2024Q1 --dest-profile prod --source-bucket company-data-db --dest-bucket company-archive --cleanup --base-local-path /mnt/data/scratch
```
This backs up a specific nested folder path (Projects/TeamA/2024Q1) showing how to target deeply nested directories.

## Reference Database Backups

### Example 5: Backing up a reference database
```bash
python backup_s3.py RefData --dest-profile prod --source-bucket company-reference-db --dest-bucket company-archive --cleanup --base-local-path /mnt/data/scratch
```
This backs up the RefData reference database.

### Example 6: Backing up a nested reference database
```bash
python backup_s3.py References/External/2024 --dest-profile prod --source-bucket company-data-db --dest-bucket company-archive --cleanup --base-local-path /mnt/data/scratch
```
This backs up a specific year of external reference data from a nested folder structure.

## Script and Resource Backups

### Example 7: Backing up analysis scripts
```bash
python backup_s3.py scripts --dest-profile prod --source-bucket company-scripts --dest-bucket company-archive --cleanup --base-local-path /mnt/data/scratch
```
This backs up analysis scripts from a scripts bucket.

### Example 8: Backing up configuration files in nested folders
```bash
python backup_s3.py Config/Environments/Production --dest-profile prod --source-bucket company-config --dest-bucket company-archive --cleanup --base-local-path /mnt/data/scratch
```
This backs up production configuration files stored in a nested folder structure.

## Configuration Options

- `--dest-profile`: AWS profile for destination bucket (required)
- `--source-bucket`: Source S3 bucket name (required)
- `--dest-bucket`: Destination S3 bucket name (required)
- `--cleanup`: Remove temporary local files after backup (optional)
- `--base-local-path`: Local path for temporary storage (required)

## Multiple DB Backups

To back up multiple databases, you can create a shell script that runs each command in sequence:

```bash
#!/bin/bash

# Define common parameters
DEST_PROFILE="prod"
SOURCE_BUCKET="company-data-db"
DEST_BUCKET="company-archive"
LOCAL_PATH="/mnt/data/scratch"

# Back up multiple folders including nested paths
python backup_s3.py Analysis --dest-profile $DEST_PROFILE --source-bucket $SOURCE_BUCKET --dest-bucket $DEST_BUCKET --cleanup --base-local-path $LOCAL_PATH
python backup_s3.py Metadata --dest-profile $DEST_PROFILE --source-bucket $SOURCE_BUCKET --dest-bucket $DEST_BUCKET --cleanup --base-local-path $LOCAL_PATH
python backup_s3.py Projects/TeamA/2024Q1 --dest-profile $DEST_PROFILE --source-bucket $SOURCE_BUCKET --dest-bucket $DEST_BUCKET --cleanup --base-local-path $LOCAL_PATH
python backup_s3.py Projects/TeamB/2024Q1 --dest-profile $DEST_PROFILE --source-bucket $SOURCE_BUCKET --dest-bucket $DEST_BUCKET --cleanup --base-local-path $LOCAL_PATH
python backup_s3.py References/External/2024 --dest-profile $DEST_PROFILE --source-bucket $SOURCE_BUCKET --dest-bucket $DEST_BUCKET --cleanup --base-local-path $LOCAL_PATH
```

This script will run five backup operations in sequence, including several with nested folder paths.