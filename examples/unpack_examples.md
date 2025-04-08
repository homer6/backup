# Unpack Examples

This document provides practical examples of using the `unpack` utility for different restoration scenarios.

## Basic Usage

The most basic usage of the `unpack` utility is to download archives from S3 and extract them to a local folder:

```bash
python unpack.py /path/to/destination_folder --s3-path s3://my-bucket/packed_folders/my_folder/20250407_120000
```

This will:
1. Download the DAR archives from the specified S3 path
2. Extract the contents to the destination folder

## Using Different AWS Profiles

If you need to use a specific AWS profile for accessing the source bucket:

```bash
python unpack.py /path/to/destination_folder --s3-path s3://company-backups/projects/project_name/20250407_120000 --source-profile backup-account
```

## Automatic Cleanup

To automatically clean up downloaded archive files after successful extraction:

```bash
python unpack.py /path/to/destination_folder --s3-path s3://my-bucket/packed_folders/my_folder/20250407_120000 --cleanup
```

## Interactive Confirmation

For critical restorations where you want to confirm each step:

```bash
python unpack.py /path/to/destination_folder --s3-path s3://my-bucket/packed_folders/important_data/20250407_120000 --confirm
```

## Resumable Restoration

If a restoration process is interrupted, you can resume it later:

```bash
# The utility will automatically detect and resume from the last checkpoint
python unpack.py /path/to/destination_folder --s3-path s3://my-bucket/packed_folders/my_folder/20250407_120000

# If you want to force a fresh restoration instead of resuming
python unpack.py /path/to/destination_folder --s3-path s3://my-bucket/packed_folders/my_folder/20250407_120000 --no-resume
```

## Custom Checkpointing

You can specify a custom checkpoint file location:

```bash
python unpack.py /path/to/destination_folder --s3-path s3://my-bucket/packed_folders/my_folder/20250407_120000 --checkpoint-file /path/to/my_checkpoint.json
```

## Custom Download Staging Location

To specify where the temporary downloaded archive files should be stored:

```bash
python unpack.py /path/to/destination_folder --s3-path s3://my-bucket/packed_folders/my_folder/20250407_120000 --base-download-path /tmp/download_staging
```

## Complete Example with Multiple Options

A comprehensive example combining multiple options:

```bash
python unpack.py /path/to/restored_project \
  --s3-path s3://company-backups/projects/project_name/20250407_120000 \
  --source-profile backup-account \
  --cleanup \
  --confirm \
  --base-download-path /tmp/download_staging
```

## Restoring Specific Backups

To restore a specific backup by using its timestamp:

```bash
# Find available backups first (using AWS CLI)
aws s3 ls s3://my-bucket/packed_folders/my_folder/ --profile backup-profile

# Then restore the specific timestamp you want
python unpack.py /path/to/destination_folder --s3-path s3://my-bucket/packed_folders/my_folder/20250407_120000 --source-profile backup-profile
```