#!/usr/bin/env python3

import argparse
import sys
import os
from backup_utils.pack_utils import UnpackUtility

def main():
    # --- Argument Parsing ---
    parser = argparse.ArgumentParser(description="Download DAR archives from S3 and unpack them to a local folder.")
    parser.add_argument("destination_folder", help="Path to the destination folder where archives should be unpacked.")
    parser.add_argument("--s3-path", required=True, help="S3 path to the archives (e.g., 's3://bucket-name/path/to/archives').")
    parser.add_argument("--cleanup", action="store_true", help="Remove the downloaded archive files after successful unpacking.")
    parser.add_argument("--confirm", action="store_true", help="Confirm each step before execution.")
    
    # Checkpoint arguments
    parser.add_argument("--checkpoint-file", default="", help="Path to checkpoint file to save progress. By default, a file based on inputs will be used.")
    parser.add_argument("--no-resume", action="store_true", help="Don't resume from previous checkpoint, even if one exists.")
    
    # AWS parameters
    parser.add_argument("--source-profile", default="", help="AWS profile for source bucket.")
    parser.add_argument("--base-download-path", default="", help="Base directory on local machine for downloaded archives (default: ~/unpack_staging).")

    args = parser.parse_args()
    
    # Validate destination folder
    dest_folder = os.path.abspath(args.destination_folder)
    os.makedirs(dest_folder, exist_ok=True)
    
    # Parse S3 path
    if not args.s3_path.startswith("s3://"):
        print("Error: S3 path must start with 's3://'", file=sys.stderr)
        sys.exit(1)
        
    s3_parts = args.s3_path[5:].split('/', 1)
    if len(s3_parts) < 2:
        print("Error: S3 path must include both bucket name and path", file=sys.stderr)
        sys.exit(1)
        
    source_bucket = s3_parts[0]
    source_path = s3_parts[1]
    
    # Create an UnpackUtility instance with configuration
    unpack = UnpackUtility(
        destination_folder=dest_folder,
        source_profile=args.source_profile,
        source_bucket=source_bucket,
        source_path=source_path,
        base_download_path=args.base_download_path or None,
        checkpoint_file=args.checkpoint_file,
        resume=not args.no_resume
    )
    
    # Perform the download and unpacking
    success = unpack.perform_unpack(
        cleanup=args.cleanup,
        confirm=args.confirm
    )
    
    if not success:
        sys.exit(1)

if __name__ == "__main__":
    main()