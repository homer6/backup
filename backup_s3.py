#!/usr/bin/env python3

import argparse
import os
import subprocess
import sys
import shutil
import configparser

# --- Configuration ---
# TODO: Verify these profile names and bucket names match your setup.
# Set to "" (empty string) to use default AWS credentials/profile.
SOURCE_PROFILE = ""
DEST_PROFILE = "prod-3"

SOURCE_BUCKET = "studies-db-prod"
DEST_BUCKET = "newatlantis-science"

# Destination path structure within the target bucket.
DEST_BUCKET_BASE_PATH = SOURCE_BUCKET # e.g., s3://dest_bucket/src_bucket_name/folder/

# Base directory on your local machine for temporary downloads.
BASE_LOCAL_PATH = os.path.expanduser("~/s3_backup_staging")

# --- Helper Functions ---

def run_command(command_list, step_description):
    """Executes a command using subprocess and handles errors."""
    print(f"         Executing: {' '.join(command_list)}")
    try:
        result = subprocess.run(command_list, check=True, capture_output=True, text=True)
        print(f"         Output:\n{result.stdout}")
        if result.stderr:
            print(f"         Warnings/Errors:\n{result.stderr}", file=sys.stderr)
        print(f"         {step_description} successful.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error during {step_description}: Command failed with exit code {e.returncode}", file=sys.stderr)
        print(f"  Command: {' '.join(e.cmd)}", file=sys.stderr)
        print(f"  Stderr:\n{e.stderr}", file=sys.stderr)
        print(f"  Stdout:\n{e.stdout}", file=sys.stderr)
        return False
    except FileNotFoundError:
        print(f"Error: The command '{command_list[0]}' was not found. Is it installed and in PATH?", file=sys.stderr)
        return False
    except Exception as e:
        print(f"An unexpected error occurred during {step_description}: {e}", file=sys.stderr)
        return False

def check_aws_cli():
    """Checks if the AWS CLI command is available."""
    if shutil.which("aws") is None:
        print("Error: AWS CLI command ('aws') not found.", file=sys.stderr)
        print("Please ensure the AWS CLI v2 is installed and in your PATH.", file=sys.stderr)
        # Add installation hints if desired
        return False
    print("AWS CLI found.")
    return True

def check_profile_exists(profile_name):
    """Checks if a named profile exists in standard AWS config/credentials files."""
    if not profile_name: # Don't check if profile name is blank (use default)
        return True

    config_path = os.path.expanduser(os.environ.get("AWS_CONFIG_FILE", "~/.aws/config"))
    creds_path = os.path.expanduser(os.environ.get("AWS_SHARED_CREDENTIALS_FILE", "~/.aws/credentials"))

    config = configparser.ConfigParser()
    creds = configparser.ConfigParser()

    config_exists = os.path.exists(config_path)
    creds_exists = os.path.exists(creds_path)

    if config_exists:
        config.read(config_path)
    if creds_exists:
        creds.read(creds_path)

    # Profile section names can be like "[profile myprofile]" in config or "[myprofile]" in credentials
    profile_section_config = f"profile {profile_name}"
    profile_section_creds = profile_name

    if (config_exists and profile_section_config in config) or \
       (creds_exists and profile_section_creds in creds):
        print(f"AWS profile '{profile_name}' found.")
        return True
    else:
        print(f"Error: AWS profile '{profile_name}' not found in {config_path} or {creds_path}.", file=sys.stderr)
        print(f"Please configure it using: aws configure --profile {profile_name}", file=sys.stderr)
        return False

# --- Main Script Logic ---

def main():
    # --- Argument Parsing ---
    parser = argparse.ArgumentParser(description="Backup a specific S3 folder from one AWS account/bucket to another via local staging.")
    parser.add_argument("folder_name", help="The specific 'folder' (prefix) within the source bucket to back up (e.g., Bermuda).")
    parser.add_argument("--cleanup", action="store_true", help="Remove the local staging directory after successful upload.")
    parser.add_argument("--use-delete", action="store_true", help="Use the --delete flag with 'aws s3 sync' during download (removes local files not in source).")

    args = parser.parse_args()
    folder_to_backup = args.folder_name

    # --- Construct Paths ---
    # Ensure trailing slash for S3 prefixes
    source_s3_path = f"s3://{SOURCE_BUCKET}/{folder_to_backup}/"
    dest_s3_path = f"s3://{DEST_BUCKET}/{DEST_BUCKET_BASE_PATH}/{folder_to_backup}/"
    # Local directory for staging
    local_download_dir = os.path.join(BASE_LOCAL_PATH, SOURCE_PROFILE or "default", SOURCE_BUCKET, folder_to_backup)

    # --- Pre-run Checks ---
    print("--- Performing Pre-run Checks ---")
    if not check_aws_cli():
        sys.exit(1)
    if not check_profile_exists(SOURCE_PROFILE):
         # If SOURCE_PROFILE is blank, check_profile_exists returns True, so this won't trigger.
         # It only checks existence if a profile name is actually provided.
        sys.exit(1)
    if not check_profile_exists(DEST_PROFILE):
        # Same logic as above for DEST_PROFILE.
        sys.exit(1)
    print("--- Pre-run Checks Passed ---")

    # --- Main Backup Process ---
    print("==================================================")
    print(f"Starting S3 Backup for Folder: {folder_to_backup}")
    print(f"  Source Profile:      {SOURCE_PROFILE or 'Default'}")
    print(f"  Source Path:         {source_s3_path}")
    print(f"  Destination Profile: {DEST_PROFILE or 'Default'}")
    print(f"  Destination Path:    {dest_s3_path}")
    print(f"  Local Staging:       {local_download_dir}")
    print(f"  Use --delete flag:   {args.use_delete}")
    print(f"  Cleanup Local Dir:   {args.cleanup}")
    print("==================================================")

    # 1. Create local staging directory
    print("[Step 1/3] Creating local staging directory...")
    try:
        os.makedirs(local_download_dir, exist_ok=True)
        print(f"         Directory ensured: {local_download_dir}")
    except OSError as e:
        print(f"Error creating directory {local_download_dir}: {e}", file=sys.stderr)
        sys.exit(1)

    # 2. Download data from source S3
    print("[Step 2/3] Downloading data from source S3...")
    download_cmd = ["aws", "s3", "sync", source_s3_path, local_download_dir]
    if SOURCE_PROFILE:
        download_cmd.extend(["--profile", SOURCE_PROFILE])
    if args.use_delete:
        download_cmd.append("--delete") # Add delete flag if requested

    if not run_command(download_cmd, "S3 download"):
        print("Aborting due to download error.", file=sys.stderr)
        sys.exit(1)

    # 3. Upload data to destination S3
    print("[Step 3/3] Uploading data to destination S3...")
    upload_cmd = ["aws", "s3", "sync", local_download_dir, dest_s3_path]
    if DEST_PROFILE:
        upload_cmd.extend(["--profile", DEST_PROFILE])

    if not run_command(upload_cmd, "S3 upload"):
        print("Aborting due to upload error.", file=sys.stderr)
        sys.exit(1)

    # 4. Optional Cleanup
    if args.cleanup:
        print("[Cleanup] Removing local staging directory...")
        try:
            shutil.rmtree(local_download_dir)
            print(f"          Removed: {local_download_dir}")
            # Attempt to remove parent directories if they are empty
            try:
                # Go up level by level trying to remove empty dirs
                parent_dir = os.path.dirname(local_download_dir)
                while parent_dir != BASE_LOCAL_PATH and parent_dir != os.path.dirname(BASE_LOCAL_PATH):
                     # Stop if we reach the base path or its parent
                    os.rmdir(parent_dir)
                    print(f"          Removed empty parent: {parent_dir}")
                    parent_dir = os.path.dirname(parent_dir)
            except OSError:
                 # Expected error if directory is not empty, ignore it.
                 pass
            print("          Cleanup complete.")
        except OSError as e:
            print(f"Warning: Could not remove local directory {local_download_dir}: {e}", file=sys.stderr)


    print("==================================================")
    print(f"Backup process finished successfully for {folder_to_backup}.")
    print("==================================================")

if __name__ == "__main__":
    main()

