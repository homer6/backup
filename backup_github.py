#!/usr/bin/env python3

import argparse
import sys
import os
from backup_utils.github_backup import GitHubBackup

def main():
    # --- Argument Parsing ---
    parser = argparse.ArgumentParser(description="Backup all GitHub repositories for an organization to a local directory and push to DAR and S3 by default.")
    parser.add_argument("org_name", help="GitHub organization name to backup.")
    parser.add_argument("--local-path", default="", help="Base directory on local machine for repository backups (default: ~/github_backup_staging).")
    parser.add_argument("--include-forks", action="store_true", help="Include forked repositories in the backup.")
    parser.add_argument("--include-wikis", action="store_true", help="Download wiki pages for each repository.")
    parser.add_argument("--include-lfs", action="store_true", help="Include Git LFS objects in the clones.")
    parser.add_argument("--cleanup", action="store_true", help="Remove the local repositories after successful backup.")
    parser.add_argument("--confirm", action="store_true", help="Confirm each step before execution.")
    
    # Archive options
    parser.add_argument("--no-archives", action="store_true", help="Skip creating DAR archives of each repository.")
    parser.add_argument("--volume-size", default="1G", help="Size limit for each archive volume (e.g., '1G', '500M'). Default is 1G.")
    
    # S3 upload options
    parser.add_argument("--no-s3-upload", action="store_true", help="Skip uploading archives to S3 bucket.")
    parser.add_argument("--dest-profile", default="", help="AWS profile for S3 upload.")
    parser.add_argument("--dest-bucket", default="", help="Destination S3 bucket name (default: <org-name>-github-backups).")
    parser.add_argument("--dest-s3-path", default="", help="Destination path within the bucket (default: github_backups/<org_name>).")
    parser.add_argument("--storage-class", default="DEEP_ARCHIVE", 
                     choices=["STANDARD", "REDUCED_REDUNDANCY", "STANDARD_IA", "ONEZONE_IA", 
                              "INTELLIGENT_TIERING", "GLACIER", "DEEP_ARCHIVE", "GLACIER_IR", "EXPRESS_ONEZONE"],
                     help="Storage class for S3 objects (default: DEEP_ARCHIVE).")
    
    # Checkpoint arguments
    parser.add_argument("--checkpoint-file", default="", help="Path to checkpoint file to save progress. By default, a file based on inputs will be used.")
    parser.add_argument("--no-resume", action="store_true", help="Don't resume from previous checkpoint, even if one exists.")
    
    args = parser.parse_args()
    
    # Get GitHub token from environment variable
    github_token = os.environ.get('GITHUB_TOKEN')
    if not github_token:
        print("Error: GitHub token not found. Please set the GITHUB_TOKEN environment variable.", file=sys.stderr)
        sys.exit(1)
    
    # Set default S3 bucket name if not provided
    s3_bucket = args.dest_bucket or f"{args.org_name}-github-backups"
    
    # Create a GitHubBackup instance with configuration
    backup = GitHubBackup(
        org_name=args.org_name,
        github_token=github_token,
        base_local_path=args.local_path or None,
        include_forks=args.include_forks,
        include_wikis=args.include_wikis,
        include_lfs=args.include_lfs,
        s3_profile=args.dest_profile,
        s3_bucket=s3_bucket,
        s3_path=args.dest_s3_path,
        storage_class=args.storage_class,
        checkpoint_file=args.checkpoint_file,
        resume=not args.no_resume
    )
    
    # Perform the backup
    success = backup.perform_backup(
        create_archives=not args.no_archives,
        upload_to_s3=not args.no_s3_upload,
        cleanup=args.cleanup,
        confirm=args.confirm,
        volume_size=args.volume_size
    )
    
    if not success:
        sys.exit(1)

if __name__ == "__main__":
    main()