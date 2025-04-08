# Pack Examples

This document provides practical examples of using the `pack` utility for different backup scenarios.

## Basic Usage

The most basic usage of the `pack` utility is to archive a folder and upload it to S3:

```bash
python pack.py /path/to/my_folder
```

This will:
1. Create DAR archives of the folder with 1GB volume size
2. Upload the archives to S3 in the default location

## Customizing Storage Location

You can specify a custom bucket and path for your archives:

```bash
python pack.py /path/to/my_folder --dest-bucket my-archive-bucket --dest-path archives/my_project
```

## Adjusting Archive Size

For large folders, you might want to adjust the volume size to optimize for transfer and storage:

```bash
# Create smaller volumes for more granular storage
python pack.py /path/to/large_folder --volume-size 500M

# Create larger volumes for fewer archive files
python pack.py /path/to/huge_folder --volume-size 5G
```

## Using Different AWS Profiles

If you need to use a specific AWS profile for the destination:

```bash
python pack.py /path/to/my_folder --dest-profile backup-profile
```

## Choosing Storage Classes

You can select an appropriate storage class based on your access needs and budget:

```bash
# For data you need to access frequently
python pack.py /path/to/my_folder --storage-class STANDARD

# For data you rarely need to access
python pack.py /path/to/my_folder --storage-class DEEP_ARCHIVE

# For data with unknown or changing access patterns
python pack.py /path/to/my_folder --storage-class INTELLIGENT_TIERING
```

## Automatic Cleanup

To automatically clean up local archive files after successful upload:

```bash
python pack.py /path/to/my_folder --cleanup
```

## Interactive Confirmation

For critical backups where you want to confirm each step:

```bash
python pack.py /path/to/important_data --confirm
```

## Resumable Backups

If a backup process is interrupted, you can resume it later:

```bash
# The utility will automatically detect and resume from the last checkpoint
python pack.py /path/to/my_folder

# If you want to force a fresh backup instead of resuming
python pack.py /path/to/my_folder --no-resume
```

## Custom Checkpointing

You can specify a custom checkpoint file location:

```bash
python pack.py /path/to/my_folder --checkpoint-file /path/to/my_checkpoint.json
```

## Custom Archive Staging Location

To specify where the temporary archive files should be stored:

```bash
python pack.py /path/to/my_folder --base-archive-path /tmp/archive_staging
```

## Complete Example with Multiple Options

A comprehensive example combining multiple options:

```bash
python pack.py /path/to/project_files \
  --dest-bucket company-backups \
  --dest-path projects/project_name \
  --volume-size 2G \
  --storage-class STANDARD_IA \
  --dest-profile backup-account \
  --cleanup \
  --confirm
```