#!/usr/bin/env python3

import argparse
import sys
import os
from backup_utils.pack_utils import PackUtility

def main():
    # --- Argument Parsing ---
    parser = argparse.ArgumentParser(description="Pack a folder into DAR archives and upload to S3.")
    parser.add_argument("folder_path", help="Path to the folder to be packed and uploaded.")
    parser.add_argument("--cleanup", action="store_true", help="Remove the local archive directory after successful upload.")
    parser.add_argument("--confirm", action="store_true", help="Confirm each step before execution.")
    parser.add_argument("--volume-size", default="1G", help="Size limit for each archive volume (e.g., '1G', '500M'). Default is 1G.")
    
    # Checkpoint arguments
    parser.add_argument("--checkpoint-file", default="", help="Path to checkpoint file to save progress. By default, a file based on inputs will be used.")
    parser.add_argument("--no-resume", action="store_true", help="Don't resume from previous checkpoint, even if one exists.")
    
    # S3 destination parameters
    parser.add_argument("--dest-profile", default="", help="AWS profile for destination bucket.")
    parser.add_argument("--dest-bucket", default="", help="Destination S3 bucket name.")
    parser.add_argument("--dest-path", default="", help="Destination path within the bucket (default: derived from folder name).")
    parser.add_argument("--storage-class", default="DEEP_ARCHIVE", 
                       choices=["STANDARD", "REDUCED_REDUNDANCY", "STANDARD_IA", "ONEZONE_IA", 
                                "INTELLIGENT_TIERING", "GLACIER", "DEEP_ARCHIVE", "GLACIER_IR", "EXPRESS_ONEZONE"],
                       help="Storage class for S3 objects (default: DEEP_ARCHIVE).")
    parser.add_argument("--base-archive-path", default="", help="Base directory on local machine for archives (default: ~/pack_archive_staging).")

    args = parser.parse_args()
    
    # Validate folder path
    folder_path = os.path.abspath(args.folder_path)
    if not os.path.exists(folder_path) or not os.path.isdir(folder_path):
        print(f"Error: The specified folder '{folder_path}' does not exist or is not a directory.", file=sys.stderr)
        sys.exit(1)
    
    # Create a PackUtility instance with configuration
    pack = PackUtility(
        folder_path=folder_path,
        dest_profile=args.dest_profile,
        dest_bucket=args.dest_bucket,
        dest_bucket_path=args.dest_path,
        base_archive_path=args.base_archive_path or None,
        destination_storage_class=args.storage_class,
        checkpoint_file=args.checkpoint_file,
        resume=not args.no_resume
    )
    
    # Perform the packing and upload
    success = pack.perform_pack(
        cleanup=args.cleanup,
        confirm=args.confirm,
        volume_size=args.volume_size
    )
    
    if not success:
        sys.exit(1)

if __name__ == "__main__":
    main()