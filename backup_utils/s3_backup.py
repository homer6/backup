import os
import subprocess
import sys
import shutil
import configparser
import datetime
import glob
from backup_utils.checkpoint import CheckpointManager

class S3Backup:
    def __init__(self, source_profile="", dest_profile="", 
                 source_bucket="", dest_bucket="",
                 dest_bucket_base_path=None, base_local_path=None,
                 destination_storage_class="DEEP_ARCHIVE",
                 checkpoint_file=None, resume=True):
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
        
        # Checkpointing
        self.resume = resume
        self.checkpoint_manager = None
        self.checkpoint_file = checkpoint_file
        # We'll initialize the checkpoint manager when we know the folder to backup

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
        base_path = os.path.join(self.BASE_LOCAL_PATH, 
                           self.SOURCE_PROFILE or "default", 
                           self.SOURCE_BUCKET)
        
        # If folder_name is empty, we're backing up the entire bucket
        if not folder_name:
            return base_path
        
        return os.path.join(base_path, folder_name)

    def perform_backup(self, folder_to_backup, use_delete=False, cleanup=False, confirm=False, volume_size="1G"):
        """Perform the S3 backup process for the specified folder or entire bucket."""
        # --- Construct Paths ---
        # Initialize checkpoint file if not provided
        # Replace slashes in folder name with underscores for directory/file naming
        safe_folder_name = folder_to_backup.replace('/', '_') if folder_to_backup else "bucket"
        
        if not self.checkpoint_file:
            # Generate checkpoint file in BASE_LOCAL_PATH
            checkpoint_dir = os.path.join(self.BASE_LOCAL_PATH, ".checkpoints")
            os.makedirs(checkpoint_dir, exist_ok=True)
            self.checkpoint_file = os.path.join(
                checkpoint_dir, 
                f"{self.SOURCE_BUCKET}_{safe_folder_name}.json"
            )
            print(f"Using auto-generated checkpoint file: {self.checkpoint_file}")
        
        # Initialize checkpoint manager now that we have the filename
        self.checkpoint_manager = CheckpointManager(self.checkpoint_file)
        
        # Use existing backup ID from checkpoint or create new one
        if self.resume and self.checkpoint_manager and self.checkpoint_manager.get_backup_id():
            timestamp = self.checkpoint_manager.get_backup_id()
            print(f"Resuming backup with ID: {timestamp}")
        else:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            # Initialize checkpoint with configuration
            config = {
                "source_profile": self.SOURCE_PROFILE,
                "dest_profile": self.DEST_PROFILE,
                "source_bucket": self.SOURCE_BUCKET,
                "dest_bucket": self.DEST_BUCKET,
                "folder_to_backup": folder_to_backup,
                "dest_bucket_base_path": self.DEST_BUCKET_BASE_PATH,
                "use_delete": use_delete,
                "cleanup": cleanup,
                "volume_size": volume_size
            }
            self.checkpoint_manager.initialize(config)
        
        # Determine if we're backing up entire bucket or a specific folder
        backup_type = "entire bucket" if not folder_to_backup else f"folder: {folder_to_backup}"
        
        # Ensure trailing slash for S3 prefixes
        source_s3_path = f"s3://{self.SOURCE_BUCKET}/"
        if folder_to_backup:
            source_s3_path = f"s3://{self.SOURCE_BUCKET}/{folder_to_backup}/"
            
        # Construct destination path
        if folder_to_backup:
            dest_s3_path = f"s3://{self.DEST_BUCKET}/{self.DEST_BUCKET_BASE_PATH}/{folder_to_backup}/{timestamp}/"
        else:
            dest_s3_path = f"s3://{self.DEST_BUCKET}/{self.DEST_BUCKET_BASE_PATH}/{timestamp}/"
        
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
        print(f"Starting S3 Backup for {backup_type}")
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
        print("[Step 1/5] Creating local staging directory...")
        
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
        print("[Step 2/5] Downloading data from source S3...")
        
        # Skip download if already completed in a previous run
        if self.resume and self.checkpoint_manager and self.checkpoint_manager.is_download_complete():
            print("         Skipping download step (already completed in previous run)")
        else:
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
                
            # Mark download as complete
            if self.checkpoint_manager:
                # Get list of downloaded files for tracking
                downloaded_files = []
                for root, _, files in os.walk(local_download_dir):
                    for file in files:
                        rel_path = os.path.relpath(os.path.join(root, file), local_download_dir)
                        downloaded_files.append(rel_path)
                self.checkpoint_manager.mark_download_complete(downloaded_files)

        # 3. Create volumes with dar
        print("[Step 3/5] Creating volumes with dar...")
        
        # Replace slashes in folder name with underscores for directory naming
        safe_folder_name = folder_to_backup.replace('/', '_') if folder_to_backup else ""
        folder_part = f"_{safe_folder_name}" if safe_folder_name else ""
        archive_dir = os.path.join(self.BASE_LOCAL_PATH, f"{self.SOURCE_BUCKET}{folder_part}_{timestamp}")
        
        # Skip archive creation if already completed in a previous run
        if self.resume and self.checkpoint_manager and self.checkpoint_manager.is_archive_complete():
            print("         Skipping archive creation step (already completed in previous run)")
        else:
            try:
                os.makedirs(archive_dir, exist_ok=True)
                print(f"         Archive directory created: {archive_dir}")
            except OSError as e:
                print(f"Error creating archive directory {archive_dir}: {e}", file=sys.stderr)
                return False
            
            # Create dar archive with volumes of specified size
            # Use safe folder name for archive name too
            archive_name = f"{safe_folder_name}_{timestamp}" if folder_to_backup else f"bucket_{timestamp}"
            archive_base_name = os.path.join(archive_dir, archive_name)

            # Suppress warnings from dar
            dar_cmd = ["dar", f"-w", f"-s", volume_size, "-c", archive_base_name, "-R", local_download_dir]
            
            if confirm and not self._confirm_step("create volumes with dar", " ".join(dar_cmd)):
                print("Backup aborted by user.")
                return False
            
            if not self.run_command(dar_cmd, "Creating archive"):
                print("Aborting due to archiving error.", file=sys.stderr)
                return False
                
            # Mark archive creation as complete
            if self.checkpoint_manager:
                # Get list of archive volumes for tracking
                archive_volumes = []
                archive_pattern = os.path.join(archive_dir, f"{archive_name}.*.dar")
                for file_path in glob.glob(archive_pattern):
                    archive_volumes.append(os.path.basename(file_path))
                self.checkpoint_manager.mark_archive_complete(archive_volumes)
        
        # 4. Upload archives to destination S3
        print("[Step 4/5] Uploading archives to destination S3...")
        
        # Skip upload if already completed in a previous run
        if self.resume and self.checkpoint_manager and self.checkpoint_manager.is_upload_complete():
            print("         Skipping upload step (already completed in previous run)")
        else:
            upload_cmd = ["aws", "s3", "sync", archive_dir, dest_s3_path, "--storage-class", self.DESTINATION_STORAGE_CLASS]
            if self.DEST_PROFILE:
                upload_cmd.extend(["--profile", self.DEST_PROFILE])
                
            if confirm and not self._confirm_step("upload archives to destination S3", " ".join(upload_cmd)):
                print("Backup aborted by user.")
                return False

            if not self.run_command(upload_cmd, "S3 upload"):
                print("Aborting due to upload error.", file=sys.stderr)
                return False
                
            # Mark upload as complete
            if self.checkpoint_manager:
                # Get list of uploaded files for tracking
                # We could run aws s3 ls command to list objects, but we'll use the local files as a proxy
                uploaded_files = []
                for file in os.listdir(archive_dir):
                    if file.endswith(".dar"):
                        uploaded_files.append(file)
                self.checkpoint_manager.mark_upload_complete(uploaded_files)

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
        backup_target = f"folder: {folder_to_backup}" if folder_to_backup else "entire bucket"
        print(f"Backup process finished successfully for {backup_target}.")
        print("==================================================")
        return True