#!/usr/bin/env python3

import argparse
import sys
from backup_utils.s3_backup import S3Backup

def main():
    # --- Argument Parsing ---
    parser = argparse.ArgumentParser(description="Backup an S3 bucket or specific folder from one AWS account/bucket to another via local staging.")
    parser.add_argument("folder_name", nargs='?', default="", help="Optional: The specific 'folder' (prefix) within the source bucket to back up (e.g., my-folder). If omitted, the entire bucket will be backed up.")
    parser.add_argument("--cleanup", action="store_true", help="Remove the local staging and archive directories after successful upload.")
    parser.add_argument("--use-delete", action="store_true", help="Use the --delete flag with 'aws s3 sync' during download (removes local files not in source).")
    parser.add_argument("--confirm", action="store_true", help="Confirm each step before execution.")
    parser.add_argument("--volume-size", default="1G", help="Size limit for each archive volume (e.g., '1G', '500M'). Default is 1G.")
    
    # Checkpoint arguments
    parser.add_argument("--checkpoint-file", default="", help="Path to checkpoint file to save progress. By default, a file based on inputs will be used.")
    parser.add_argument("--no-resume", action="store_true", help="Don't resume from previous checkpoint, even if one exists.")
    
    # Additional parameters to override defaults
    parser.add_argument("--source-profile", default="", help="AWS profile for source bucket.")
    parser.add_argument("--dest-profile", default="", help="AWS profile for destination bucket.")
    parser.add_argument("--source-bucket", default="", help="Source S3 bucket name.")
    parser.add_argument("--dest-bucket", default="", help="Destination S3 bucket name.")
    parser.add_argument("--dest-path", default="", help="Destination path within the bucket (default: same as source bucket name).")
    parser.add_argument("--base-local-path", default="", help="Base directory on local machine for temporary downloads (default: ~/s3_backup_staging).")
    parser.add_argument("--storage-class", default="DEEP_ARCHIVE", 
                       choices=["STANDARD", "REDUCED_REDUNDANCY", "STANDARD_IA", "ONEZONE_IA", 
                                "INTELLIGENT_TIERING", "GLACIER", "DEEP_ARCHIVE", "GLACIER_IR", "EXPRESS_ONEZONE"],
                       help="Storage class for S3 objects (default: DEEP_ARCHIVE).")

    args = parser.parse_args()
    
    # Create an S3Backup instance with configuration
    backup = S3Backup(
        source_profile=args.source_profile,
        dest_profile=args.dest_profile,
        source_bucket=args.source_bucket,
        dest_bucket=args.dest_bucket,
        dest_bucket_base_path=args.dest_path,
        base_local_path=args.base_local_path or None,
        destination_storage_class=args.storage_class,
        checkpoint_file=args.checkpoint_file,
        resume=not args.no_resume
    )
    
    # Perform the backup
    success = backup.perform_backup(
        folder_to_backup=args.folder_name,
        use_delete=args.use_delete,
        cleanup=args.cleanup,
        confirm=args.confirm,
        volume_size=args.volume_size
    )
    
    if not success:
        sys.exit(1)

if __name__ == "__main__":
    main()