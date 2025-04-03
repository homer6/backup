# S3 Folder Backup Tool

A Python utility for backing up specific folders (S3 prefixes) from a source AWS S3 bucket to a destination S3 bucket, potentially across different AWS accounts.

## Description

This tool automates the process of backing up specific folders by:

1. Downloading the specified folder from the source bucket to a local staging directory
2. Uploading the contents to the destination bucket under a specified path structure

The tool is structured using a Python class (`S3Backup`) for better organization and reuse.

## Features

* Uses AWS CLI (`aws s3 sync`) for efficient S3 operations
* Supports using default AWS credentials or specific named profiles
* Provides clear console output during execution
* Includes basic prerequisite checks (AWS CLI availability, profile existence)
* Optional cleanup of local staging files after backup

## Prerequisites

* Python 3.6+
* AWS CLI v2 installed and accessible in your system's PATH
* AWS credentials with access to source and destination buckets

## Usage

Basic usage:
```
python backup_s3.py folder_name
```

With options:
```
python backup_s3.py folder_name --cleanup --use-delete --source-profile profile1 --dest-profile profile2
```

### Options

- `folder_name`: The S3 prefix (folder) to back up
- `--cleanup`: Remove local staging directory after successful upload
- `--use-delete`: Use the --delete flag with AWS S3 sync during download
- `--source-profile`: AWS profile for source bucket (default: use default profile)
- `--dest-profile`: AWS profile for destination bucket (default: prod-3)
- `--source-bucket`: Source S3 bucket name (default: studies-db-prod)
- `--dest-bucket`: Destination S3 bucket name (default: newatlantis-science)