# Pack Utility

The `pack` utility allows you to easily archive folders using DAR and upload the archives to S3.

## Overview

The `pack` tool takes a local folder, archives it with DAR into manageable volumes, and uploads those archives to S3. This is useful for preserving directory structures while taking advantage of DAR's efficient archive format.

## Usage

```
python pack.py <folder_path> [options]
```

## Arguments

- `folder_path`: Path to the folder to be packed and uploaded.

## Options

- `--cleanup`: Remove the local archive directory after successful upload.
- `--confirm`: Confirm each step before execution.
- `--volume-size SIZE`: Size limit for each archive volume (e.g., '1G', '500M'). Default is 1G.
- `--checkpoint-file FILE`: Path to checkpoint file to save progress. By default, a file based on inputs will be used.
- `--no-resume`: Don't resume from previous checkpoint, even if one exists.
- `--dest-profile PROFILE`: AWS profile for destination bucket.
- `--dest-bucket BUCKET`: Destination S3 bucket name.
- `--dest-path PATH`: Destination path within the bucket (default: derived from folder name).
- `--storage-class CLASS`: Storage class for S3 objects (default: DEEP_ARCHIVE).
- `--base-archive-path PATH`: Base directory on local machine for archives (default: ~/pack_archive_staging).

## Example

```bash
# Basic usage
python pack.py /home/user/important_data

# Pack with custom options
python pack.py /home/user/important_data --dest-bucket my-backups --dest-path archives/important --volume-size 500M --storage-class STANDARD
```

## Features

### Checkpointing

The utility implements checkpointing to allow operations to be resumed if interrupted. This is especially useful for large folders or when network connectivity is unreliable.

### Archive Management

The `pack` utility creates DAR archives with customizable volume sizes, making it suitable for both small and large data sets.

### AWS Integration

The utility integrates with AWS S3 for storage of archives, supporting different AWS profiles and storage classes.