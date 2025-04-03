#!/usr/bin/env python3

import argparse
import sys
from backup_utils.s3_backup import S3Backup

def main():
    # --- Argument Parsing ---
    parser = argparse.ArgumentParser(description="Backup a specific S3 folder from one AWS account/bucket to another via local staging.")
    parser.add_argument("folder_name", help="The specific 'folder' (prefix) within the source bucket to back up (e.g., my-folder).")
    parser.add_argument("--cleanup", action="store_true", help="Remove the local staging directory after successful upload.")
    parser.add_argument("--use-delete", action="store_true", help="Use the --delete flag with 'aws s3 sync' during download (removes local files not in source).")
    parser.add_argument("--confirm", action="store_true", help="Confirm each step before execution.")
    
    # Additional parameters to override defaults
    parser.add_argument("--source-profile", default="", help="AWS profile for source bucket.")
    parser.add_argument("--dest-profile", default="", help="AWS profile for destination bucket.")
    parser.add_argument("--source-bucket", default="", help="Source S3 bucket name.")
    parser.add_argument("--dest-bucket", default="", help="Destination S3 bucket name.")

    args = parser.parse_args()
    
    # Create an S3Backup instance with configuration
    backup = S3Backup(
        source_profile=args.source_profile,
        dest_profile=args.dest_profile,
        source_bucket=args.source_bucket,
        dest_bucket=args.dest_bucket
    )
    
    # Perform the backup
    success = backup.perform_backup(
        folder_to_backup=args.folder_name,
        use_delete=args.use_delete,
        cleanup=args.cleanup,
        confirm=args.confirm
    )
    
    if not success:
        sys.exit(1)

if __name__ == "__main__":
    main()