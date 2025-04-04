import os
import subprocess
import sys
import shutil
import configparser
import datetime

class S3Backup:
    def __init__(self, source_profile="", dest_profile="", 
                 source_bucket="", dest_bucket="",
                 dest_bucket_base_path=None, base_local_path=None,
                 destination_storage_class="DEEP_ARCHIVE"):
        # --- Configuration ---
        self.SOURCE_PROFILE = source_profile
        self.DEST_PROFILE = dest_profile
        
        self.SOURCE_BUCKET = source_bucket
        self.DEST_BUCKET = dest_bucket
        
        # Destination path structure within the target bucket.
        self.DEST_BUCKET_BASE_PATH = dest_bucket_base_path or source_bucket
        
        # Base directory on your local machine for temporary downloads.
        self.BASE_LOCAL_PATH = base_local_path or os.path.expanduser("~/s3_backup_staging")
        
        # S3 storage class for destination bucket
        self.DESTINATION_STORAGE_CLASS = destination_storage_class

    def _confirm_step(self, step_description, command=None):
        """Ask for user confirmation before proceeding with a step."""
        message = f"\nReady to {step_description}."
        if command:
            message += f"\nCommand: {command}"
        message += "\nProceed? (yes/no): "
        response = input(message).strip().lower()
        return response in ['yes', 'y']

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

    def perform_backup(self, folder_to_backup, use_delete=False, cleanup=False, confirm=False, volume_size="1G"):
        """Perform the S3 backup process for the specified folder."""
        # --- Construct Paths ---
        # Create timestamp for this backup
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Ensure trailing slash for S3 prefixes
        source_s3_path = f"s3://{self.SOURCE_BUCKET}/{folder_to_backup}/"
        dest_s3_path = f"s3://{self.DEST_BUCKET}/{self.DEST_BUCKET_BASE_PATH}/{folder_to_backup}/{timestamp}/"
        
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
        print(f"  Destination Storage Class: {self.DESTINATION_STORAGE_CLASS}")
        print(f"  Local Staging:       {local_download_dir}")
        print(f"  Use --delete flag:   {use_delete}")
        print(f"  Cleanup Local Dir:   {cleanup}")
        print(f"  Confirm Each Step:   {confirm}")
        print("==================================================")

        # 1. Create local staging directory
        print("[Step 1/3] Creating local staging directory...")
        
        if confirm and not self._confirm_step("create local staging directory", f"mkdir -p {local_download_dir}"):
            print("Backup aborted by user.")
            return False
            
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
            download_cmd.append("--delete")  # Add delete flag if requested; this will remove local files (at the destination) that are not in source
            
        if confirm and not self._confirm_step("download data from source S3", " ".join(download_cmd)):
            print("Backup aborted by user.")
            return False

        if not self.run_command(download_cmd, "S3 download"):
            print("Aborting due to download error.", file=sys.stderr)
            return False

        # 3. Create volumes with dar
        print("[Step 3/5] Creating volumes with dar...")
        
        # Create archive directory
        archive_dir = os.path.join(self.BASE_LOCAL_PATH, f"{self.SOURCE_BUCKET}_{folder_to_backup}_{timestamp}")
        try:
            os.makedirs(archive_dir, exist_ok=True)
            print(f"         Archive directory created: {archive_dir}")
        except OSError as e:
            print(f"Error creating archive directory {archive_dir}: {e}", file=sys.stderr)
            return False
        
        # Create dar archive with volumes of specified size
        archive_base_name = os.path.join(archive_dir, f"{folder_to_backup}_{timestamp}")
        dar_cmd = ["dar", f"-s", volume_size, "-c", archive_base_name, "-R", local_download_dir]
        
        if confirm and not self._confirm_step("create volumes with dar", " ".join(dar_cmd)):
            print("Backup aborted by user.")
            return False
        
        if not self.run_command(dar_cmd, "Creating archive"):
            print("Aborting due to archiving error.", file=sys.stderr)
            return False
        
        # 4. Upload archives to destination S3
        print("[Step 4/5] Uploading archives to destination S3...")
            
        upload_cmd = ["aws", "s3", "sync", archive_dir, dest_s3_path, "--storage-class", self.DESTINATION_STORAGE_CLASS]
        if self.DEST_PROFILE:
            upload_cmd.extend(["--profile", self.DEST_PROFILE])
            
        if confirm and not self._confirm_step("upload archives to destination S3", " ".join(upload_cmd)):
            print("Backup aborted by user.")
            return False

        if not self.run_command(upload_cmd, "S3 upload"):
            print("Aborting due to upload error.", file=sys.stderr)
            return False

        # 5. Optional Cleanup
        if cleanup:
            print("[Step 5/5] Cleaning up local directories...")
            
            # Clean up staging directory
            print("Removing local staging directory...")
            if confirm and not self._confirm_step("remove local staging directory", f"rm -rf {local_download_dir}"):
                print("Staging directory cleanup skipped by user.")
            else:
                try:
                    shutil.rmtree(local_download_dir)
                    print(f"          Removed: {local_download_dir}")
                except OSError as e:
                    print(f"Warning: Could not remove local directory {local_download_dir}: {e}", file=sys.stderr)
            
            # Clean up archive directory
            print("Removing local archive directory...")
            if confirm and not self._confirm_step("remove local archive directory", f"rm -rf {archive_dir}"):
                print("Archive directory cleanup skipped by user.")
            else:
                try:
                    shutil.rmtree(archive_dir)
                    print(f"          Removed: {archive_dir}")
                    print("          Cleanup complete.")
                except OSError as e:
                    print(f"Warning: Could not remove local directory {archive_dir}: {e}", file=sys.stderr)

        print("==================================================")
        print(f"Backup process finished successfully for {folder_to_backup}.")
        print("==================================================")
        return True