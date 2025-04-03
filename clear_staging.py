#!/usr/bin/env python3

import argparse
import os
import sys
import shutil
from backup_utils.s3_backup import S3Backup

def confirm_deletion(path):
    """Ask for confirmation before deletion."""
    print(f"\nWARNING: About to delete: {path}")
    
    if os.path.exists(path):
        # Count files to be deleted
        file_count = 0
        dir_count = 0
        for root, dirs, files in os.walk(path):
            file_count += len(files)
            dir_count += len(dirs)
        
        print(f"This will delete {file_count} files and {dir_count} directories.")
    else:
        print("WARNING: Path doesn't exist, nothing to delete.")
        return False
    
    response = input("Are you sure you want to proceed? (yes/no): ").strip().lower()
    return response in ['yes', 'y']

def clear_staging_directory(s3_backup, folder_name=None, all_folders=False, force=False):
    """Clear a specific staging directory or all staging directories."""
    base_path = s3_backup.BASE_LOCAL_PATH
    
    if not os.path.exists(base_path):
        print(f"Staging directory {base_path} doesn't exist. Nothing to do.")
        return True
    
    if all_folders:
        # Delete the entire staging base directory
        if force or confirm_deletion(base_path):
            try:
                shutil.rmtree(base_path)
                print(f"Successfully removed all staging directories: {base_path}")
                return True
            except OSError as e:
                print(f"Error removing directory {base_path}: {e}", file=sys.stderr)
                return False
        else:
            print("Operation cancelled by user.")
            return False
    
    # Specific folder deletion
    if folder_name:
        folder_path = s3_backup.get_staging_dir(folder_name)
        
        if not os.path.exists(folder_path):
            print(f"Folder path {folder_path} doesn't exist. Nothing to delete.")
            return True
        
        if force or confirm_deletion(folder_path):
            try:
                shutil.rmtree(folder_path)
                print(f"Successfully removed staging directory: {folder_path}")
                
                # Try to remove parent directories if empty (going upward until base dir)
                parent_dir = os.path.dirname(folder_path)
                while parent_dir != base_path and os.path.exists(parent_dir):
                    try:
                        os.rmdir(parent_dir)  # Will only succeed if directory is empty
                        print(f"Removed empty parent directory: {parent_dir}")
                    except OSError:
                        # Stop if directory is not empty
                        break
                    parent_dir = os.path.dirname(parent_dir)
                
                return True
            except OSError as e:
                print(f"Error removing directory {folder_path}: {e}", file=sys.stderr)
                return False
        else:
            print("Operation cancelled by user.")
            return False
    
    # If we reach here, no action was specified
    print("No action taken. Specify --folder or --all to clear staging directories.")
    return True

def main():
    parser = argparse.ArgumentParser(description="Clear S3 backup staging directories")
    parser.add_argument("--folder", help="Specific folder to clear from staging")
    parser.add_argument("--all", action="store_true", help="Clear all staging directories")
    parser.add_argument("--force", action="store_true", help="Skip confirmation prompts")
    
    # Additional parameters matching the backup script
    parser.add_argument("--source-profile", default="", help="AWS profile for source bucket")
    parser.add_argument("--source-bucket", default="studies-db-prod", help="Source S3 bucket name")
    parser.add_argument("--staging-path", help="Override default staging path")
    
    args = parser.parse_args()
    
    if not args.folder and not args.all:
        parser.print_help()
        print("\nERROR: You must specify either --folder or --all", file=sys.stderr)
        sys.exit(1)
    
    # Create backup instance to access the staging directories
    backup = S3Backup(
        source_profile=args.source_profile,
        source_bucket=args.source_bucket,
        base_local_path=args.staging_path
    )
    
    success = clear_staging_directory(
        s3_backup=backup,
        folder_name=args.folder,
        all_folders=args.all,
        force=args.force
    )
    
    if not success:
        sys.exit(1)

if __name__ == "__main__":
    main()