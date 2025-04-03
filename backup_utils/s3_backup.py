import os
import subprocess
import sys
import shutil
import configparser

class S3Backup:
    def __init__(self, source_profile="", dest_profile="prod-3", 
                 source_bucket="studies-db-prod", dest_bucket="newatlantis-science",
                 dest_bucket_base_path=None, base_local_path=None):
        # --- Configuration ---
        self.SOURCE_PROFILE = source_profile
        self.DEST_PROFILE = dest_profile
        
        self.SOURCE_BUCKET = source_bucket
        self.DEST_BUCKET = dest_bucket
        
        # Destination path structure within the target bucket.
        self.DEST_BUCKET_BASE_PATH = dest_bucket_base_path or source_bucket
        
        # Base directory on your local machine for temporary downloads.
        self.BASE_LOCAL_PATH = base_local_path or os.path.expanduser("~/s3_backup_staging")

    def run_command(self, command_list, step_description):
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

    def check_aws_cli(self):
        """Checks if the AWS CLI command is available."""
        if shutil.which("aws") is None:
            print("Error: AWS CLI command ('aws') not found.", file=sys.stderr)
            print("Please ensure the AWS CLI v2 is installed and in your PATH.", file=sys.stderr)
            return False
        print("AWS CLI found.")
        return True

    def check_profile_exists(self, profile_name):
        """Checks if a named profile exists in standard AWS config/credentials files."""
        if not profile_name:  # Don't check if profile name is blank (use default)
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

    def get_staging_dir(self, folder_name):
        """Returns the local staging directory path for a given folder."""
        return os.path.join(self.BASE_LOCAL_PATH, 
                           self.SOURCE_PROFILE or "default", 
                           self.SOURCE_BUCKET, 
                           folder_name)

    def perform_backup(self, folder_to_backup, use_delete=False, cleanup=False):
        """Perform the S3 backup process for the specified folder."""
        # --- Construct Paths ---
        # Ensure trailing slash for S3 prefixes
        source_s3_path = f"s3://{self.SOURCE_BUCKET}/{folder_to_backup}/"
        dest_s3_path = f"s3://{self.DEST_BUCKET}/{self.DEST_BUCKET_BASE_PATH}/{folder_to_backup}/"
        # Local directory for staging
        local_download_dir = self.get_staging_dir(folder_to_backup)

        # --- Pre-run Checks ---
        print("--- Performing Pre-run Checks ---")
        if not self.check_aws_cli():
            return False
        if not self.check_profile_exists(self.SOURCE_PROFILE):
            return False
        if not self.check_profile_exists(self.DEST_PROFILE):
            return False
        print("--- Pre-run Checks Passed ---")

        # --- Main Backup Process ---
        print("==================================================")
        print(f"Starting S3 Backup for Folder: {folder_to_backup}")
        print(f"  Source Profile:      {self.SOURCE_PROFILE or 'Default'}")
        print(f"  Source Path:         {source_s3_path}")
        print(f"  Destination Profile: {self.DEST_PROFILE or 'Default'}")
        print(f"  Destination Path:    {dest_s3_path}")
        print(f"  Local Staging:       {local_download_dir}")
        print(f"  Use --delete flag:   {use_delete}")
        print(f"  Cleanup Local Dir:   {cleanup}")
        print("==================================================")

        # 1. Create local staging directory
        print("[Step 1/3] Creating local staging directory...")
        try:
            os.makedirs(local_download_dir, exist_ok=True)
            print(f"         Directory ensured: {local_download_dir}")
        except OSError as e:
            print(f"Error creating directory {local_download_dir}: {e}", file=sys.stderr)
            return False

        # 2. Download data from source S3
        print("[Step 2/3] Downloading data from source S3...")
        download_cmd = ["aws", "s3", "sync", source_s3_path, local_download_dir]
        if self.SOURCE_PROFILE:
            download_cmd.extend(["--profile", self.SOURCE_PROFILE])
        if use_delete:
            download_cmd.append("--delete")  # Add delete flag if requested

        if not self.run_command(download_cmd, "S3 download"):
            print("Aborting due to download error.", file=sys.stderr)
            return False

        # 3. Upload data to destination S3
        print("[Step 3/3] Uploading data to destination S3...")
        upload_cmd = ["aws", "s3", "sync", local_download_dir, dest_s3_path]
        if self.DEST_PROFILE:
            upload_cmd.extend(["--profile", self.DEST_PROFILE])

        if not self.run_command(upload_cmd, "S3 upload"):
            print("Aborting due to upload error.", file=sys.stderr)
            return False

        # 4. Optional Cleanup
        if cleanup:
            print("[Cleanup] Removing local staging directory...")
            try:
                shutil.rmtree(local_download_dir)
                print(f"          Removed: {local_download_dir}")
                print("          Cleanup complete.")
            except OSError as e:
                print(f"Warning: Could not remove local directory {local_download_dir}: {e}", file=sys.stderr)

        print("==================================================")
        print(f"Backup process finished successfully for {folder_to_backup}.")
        print("==================================================")
        return True