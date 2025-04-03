# S3 Folder Backup Script (backup_s3.py)

## Description

This Python script automates the process of backing up specific folders (S3 prefixes) from a source AWS S3 bucket to a destination S3 bucket, potentially across different AWS accounts. It works by:

1.  Downloading the specified folder from the source bucket to a local staging directory.
2.  Uploading the contents of the local staging directory to the destination bucket, placing it under a path structure that includes the source bucket name, the original folder name, and a **timestamp** (YYYYMMDD_HHMMSS) for versioning.

The script is structured using a Python class (`S3Backup`) for better organization.

## Features

* Uses AWS CLI (`aws s3 sync`) for efficient S3 operations.
* Supports using default AWS credentials or specific named profiles for both source and destination operations.
* Automatically adds a timestamp to the destination path for each backup run.
* Organized using a Python class structure.
* Provides clear console output during execution.
* Includes basic prerequisite checks (AWS CLI availability, profile existence if specified).

## Prerequisites

Before running this script, ensure you have the following:

1.  **Python 3:** The script is written for Python 3.
2.  **AWS CLI v2:** The AWS Command Line Interface (version 2 recommended) must be installed and accessible in your system's PATH.
3.  **AWS Credentials:** Configure your AWS credentials. The script relies on the AWS CLI's credential handling:
    * **Default Credentials:** If `SOURCE_PROFILE` is set to `""` (empty string), the script uses the default credentials configured for your environment (e.g., via environment variables `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, etc., the `[default]` section in `~/.aws/credentials`, or an IAM role attached to an EC2 instance/ECS task).
    * **Named Profiles:** If `SOURCE_PROFILE` or `DEST_PROFILE` are set to specific profile names (e.g., `"prod-3"`), ensure those profiles are configured using `aws configure --profile <profile_name>`.

## Configuration

Modify the configuration variables directly within the `S3Backup` class in the `backup_s3.py` script:

* `SOURCE_PROFILE`: Set to the AWS profile name for accessing the source bucket, or `""` to use default credentials.
* `DEST_PROFILE`: Set to the AWS profile name for accessing the destination bucket, or `""` to use default credentials.
* `SOURCE_BUCKET`: The name of the source S3 bucket.
* `DEST_BUCKET`: The name of the destination S3 bucket.
* `DEST_BUCKET_BASE_PATH`: A base path within the destination bucket where the backed-up data will be stored (defaults to the source bucket name). The final path will be `s3://{DEST_BUCKET}/{DEST_BUCKET_BASE_PATH}/{folder_name}/{timestamp}/`.
* `BASE_LOCAL_PATH`: The base path on your local machine where temporary staging directories will be created (defaults to `~/s3_backup_staging`).
* `TIMESTAMP_FORMAT`: The format string for the timestamp used in the destination path (defaults to `"%Y%m%d_%H%M%S"`).

## Usage

Run the script from your terminal, providing the name of the S3 folder (prefix) you want to back up as a command-line argument.

**Syntax:**

```bash
python3 backup_s3.py <folder_name>
Or, if you've made the script executable (chmod +x backup_s3.py):./backup_s3.py <folder_name>
Examples:# Back up the 'Bermuda' folder from the source bucket
./backup_s3.py Bermuda

# Back up the 'ProjectXFiles' folder
python3 backup_s3.py ProjectXFiles
To see help and examples:./backup_s3.py -h
How it WorksInitialization: Parses the command-line argument (folder_name).Prerequisites Check: Verifies AWS CLI installation and profile existence (if profiles are specified).Timestamp Generation: Creates a timestamp string.Path Construction: Builds the source S3 path, timestamped destination S3 path, and local staging directory path.Local Directory Creation: Ensures the local staging directory exists.Download: Executes aws s3 sync to download data from the source S3 path to the local staging directory using the source credentials/profile.Upload: Executes aws s3 sync to upload data from the local staging directory to the timestamped destination S3 path using the destination credentials/profile.Important NotesNo Deletion: This script does not delete the source data or the local staging data after the backup completes. The local data remains in the directory specified by BASE_LOCAL_PATH.Efficiency: Downloading data locally and re-uploading is less efficient than a direct S3-to-S3 copy. For large