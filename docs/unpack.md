# Unpack Utility

The `unpack` utility allows you to retrieve archived folders from S3 and restore them to your local filesystem.

## Overview

The `unpack` tool downloads DAR archives from S3 and extracts them to a specified local folder, effectively reversing the process performed by the `pack` utility.

## Usage

```
python unpack.py <destination_folder> --s3-path <s3-path> [options]
```

## Arguments

- `destination_folder`: Path to the destination folder where archives should be unpacked.
- `--s3-path`: S3 path to the archives (e.g., 's3://bucket-name/path/to/archives').

## Options

- `--cleanup`: Remove the downloaded archive files after successful unpacking.
- `--confirm`: Confirm each step before execution.
- `--checkpoint-file FILE`: Path to checkpoint file to save progress. By default, a file based on inputs will be used.
- `--no-resume`: Don't resume from previous checkpoint, even if one exists.
- `--source-profile PROFILE`: AWS profile for source bucket.
- `--base-download-path PATH`: Base directory on local machine for downloaded archives (default: ~/unpack_staging).

## Example

```bash
# Basic usage
python unpack.py /home/user/restored_data --s3-path s3://my-backups/packed_folders/important_data/20250407_120000

# Unpack with custom options
python unpack.py /home/user/restored_data --s3-path s3://my-backups/archives/important/20250407_120000 --source-profile backup-profile --cleanup
```

## Features

### Checkpointing

The utility implements checkpointing to allow operations to be resumed if interrupted. This is especially useful for large archives or when network connectivity is unreliable.

### Archive Management

The `unpack` utility handles DAR archives of any volume size, automatically detecting and extracting all parts of the archive.

### AWS Integration

The utility integrates with AWS S3 for retrieval of archives, supporting different AWS profiles.