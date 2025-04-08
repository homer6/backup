import os
import subprocess
import sys
import shutil
import configparser
import datetime
import glob
from backup_utils.checkpoint import CheckpointManager

class PackUtility:
    def __init__(self, folder_path, dest_profile="", dest_bucket="",
                 dest_bucket_path=None, base_archive_path=None,
                 destination_storage_class="DEEP_ARCHIVE",
                 checkpoint_file=None, resume=True):
        # --- Configuration ---
        self.FOLDER_PATH = folder_path
        self.FOLDER_NAME = os.path.basename(os.path.normpath(folder_path))
        
        self.DEST_PROFILE = dest_profile
        self.DEST_BUCKET = dest_bucket
        
        # Destination path structure within the target bucket
        self.DEST_BUCKET_PATH = dest_bucket_path or f"packed_folders/{self.FOLDER_NAME}"
        
        # Base directory on local machine for archives
        self.BASE_ARCHIVE_PATH = base_archive_path or os.path.expanduser("~/pack_archive_staging")
        
        # S3 storage class for destination bucket
        self.DESTINATION_STORAGE_CLASS = destination_storage_class
        
        # Checkpointing
        self.resume = resume
        self.checkpoint_manager = None
        self.checkpoint_file = checkpoint_file
        # We'll initialize the checkpoint manager in perform_pack
    
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
    
    def check_dar_cli(self):
        """Checks if the DAR command is available."""
        if shutil.which("dar") is None:
            print("Error: DAR command ('dar') not found.", file=sys.stderr)
            print("Please ensure DAR is installed and in your PATH.", file=sys.stderr)
            return False
        print("DAR command found.")
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

    def perform_pack(self, cleanup=False, confirm=False, volume_size="1G"):
        """Pack the folder into DAR archives and upload to S3."""
        # --- Initialize Checkpoint ---
        # Generate timestamp for this pack operation
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Initialize checkpoint file if not provided
        if not self.checkpoint_file:
            # Generate checkpoint file in BASE_ARCHIVE_PATH
            checkpoint_dir = os.path.join(self.BASE_ARCHIVE_PATH, ".checkpoints")
            os.makedirs(checkpoint_dir, exist_ok=True)
            self.checkpoint_file = os.path.join(
                checkpoint_dir, 
                f"pack_{self.FOLDER_NAME}.json"
            )
            print(f"Using auto-generated checkpoint file: {self.checkpoint_file}")
        
        # Initialize checkpoint manager now that we have the filename
        self.checkpoint_manager = CheckpointManager(self.checkpoint_file)
        
        # Use existing backup ID from checkpoint or create new one
        if self.resume and self.checkpoint_manager and self.checkpoint_manager.get_backup_id():
            timestamp = self.checkpoint_manager.get_backup_id()
            print(f"Resuming pack operation with ID: {timestamp}")
        else:
            # Initialize checkpoint with configuration
            config = {
                "folder_path": self.FOLDER_PATH,
                "folder_name": self.FOLDER_NAME,
                "dest_profile": self.DEST_PROFILE,
                "dest_bucket": self.DEST_BUCKET,
                "dest_bucket_path": self.DEST_BUCKET_PATH,
                "cleanup": cleanup,
                "volume_size": volume_size
            }
            self.checkpoint_manager.initialize(config)
        
        # --- Construct Paths ---
        # Archive directory
        archive_dir = os.path.join(self.BASE_ARCHIVE_PATH, f"{self.FOLDER_NAME}_{timestamp}")
        
        # Construct S3 destination path
        dest_s3_path = f"s3://{self.DEST_BUCKET}/{self.DEST_BUCKET_PATH}/{timestamp}/"
        
        # --- Pre-run Checks ---
        print("--- Performing Pre-run Checks ---")
        if not self.check_dar_cli():
            return False
        if not self.check_aws_cli():
            return False
        if not self.check_profile_exists(self.DEST_PROFILE):
            return False
        print("--- Pre-run Checks Passed ---")
        
        # --- Main Pack Process ---
        print("==================================================")
        print(f"Starting Pack Operation for folder: {self.FOLDER_PATH}")
        print(f"  Destination Profile: {self.DEST_PROFILE or 'Default'}")
        print(f"  Destination Bucket:  {self.DEST_BUCKET}")
        print(f"  Destination Path:    {dest_s3_path}")
        print(f"  Storage Class:       {self.DESTINATION_STORAGE_CLASS}")
        print(f"  Archive Directory:   {archive_dir}")
        print(f"  Volume Size:         {volume_size}")
        print(f"  Cleanup Archives:    {cleanup}")
        print(f"  Confirm Each Step:   {confirm}")
        print("==================================================")
        
        # 1. Create archive directory
        print("[Step 1/3] Creating archive directory...")
        
        if confirm and not self._confirm_step("create archive directory", f"mkdir -p {archive_dir}"):
            print("Pack operation aborted by user.")
            return False
            
        try:
            os.makedirs(archive_dir, exist_ok=True)
            print(f"         Directory created: {archive_dir}")
        except OSError as e:
            print(f"Error creating directory {archive_dir}: {e}", file=sys.stderr)
            return False
        
        # 2. Create archive with dar
        print("[Step 2/3] Creating DAR archives...")
        
        # Skip archive creation if already completed in a previous run
        if self.resume and self.checkpoint_manager and self.checkpoint_manager.is_archive_complete():
            print("         Skipping archive creation step (already completed in previous run)")
        else:
            # Create archive with dar
            archive_name = f"{self.FOLDER_NAME}_{timestamp}"
            archive_base = os.path.join(archive_dir, archive_name)
            
            # Create dar archive with volumes of specified size
            dar_cmd = ["dar", "-w", "-s", volume_size, "-c", archive_base, "-R", self.FOLDER_PATH]
            
            if confirm and not self._confirm_step("create DAR archives", " ".join(dar_cmd)):
                print("Pack operation aborted by user.")
                return False
            
            if not self.run_command(dar_cmd, "Creating archives"):
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
        
        # 3. Upload archives to S3
        print("[Step 3/3] Uploading archives to S3...")
        
        # Skip upload if already completed in a previous run
        if self.resume and self.checkpoint_manager and self.checkpoint_manager.is_upload_complete():
            print("         Skipping upload step (already completed in previous run)")
        else:
            # Upload archives to S3
            upload_cmd = ["aws", "s3", "sync", archive_dir, dest_s3_path, "--storage-class", self.DESTINATION_STORAGE_CLASS]
            if self.DEST_PROFILE:
                upload_cmd.extend(["--profile", self.DEST_PROFILE])
                
            if confirm and not self._confirm_step("upload archives to S3", " ".join(upload_cmd)):
                print("Pack operation aborted by user.")
                return False
            
            if not self.run_command(upload_cmd, "S3 upload"):
                print("Aborting due to upload error.", file=sys.stderr)
                return False
                
            # Mark upload as complete
            if self.checkpoint_manager:
                # Get list of uploaded files for tracking
                uploaded_files = []
                for file in os.listdir(archive_dir):
                    if file.endswith(".dar"):
                        uploaded_files.append(file)
                self.checkpoint_manager.mark_upload_complete(uploaded_files)
        
        # 4. Optional Cleanup
        if cleanup:
            print("[Cleanup] Removing local archive directory...")
            
            if confirm and not self._confirm_step("remove local archive directory", f"rm -rf {archive_dir}"):
                print("Archive directory cleanup skipped by user.")
            else:
                try:
                    shutil.rmtree(archive_dir)
                    print(f"         Removed: {archive_dir}")
                    print("         Cleanup complete.")
                except OSError as e:
                    print(f"Warning: Could not remove local directory {archive_dir}: {e}", file=sys.stderr)
        
        print("==================================================")
        print(f"Pack operation completed successfully for folder: {self.FOLDER_PATH}")
        print(f"Archives uploaded to: {dest_s3_path}")
        print("==================================================")
        return True


class UnpackUtility:
    def __init__(self, destination_folder, source_profile="", source_bucket="",
                 source_path="", base_download_path=None,
                 checkpoint_file=None, resume=True):
        # --- Configuration ---
        self.DESTINATION_FOLDER = destination_folder
        self.SOURCE_PROFILE = source_profile
        self.SOURCE_BUCKET = source_bucket
        self.SOURCE_PATH = source_path
        
        # Base directory on local machine for downloaded archives
        self.BASE_DOWNLOAD_PATH = base_download_path or os.path.expanduser("~/unpack_staging")
        
        # Checkpointing
        self.resume = resume
        self.checkpoint_manager = None
        self.checkpoint_file = checkpoint_file
        # We'll initialize the checkpoint manager in perform_unpack
    
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
    
    def check_dar_cli(self):
        """Checks if the DAR command is available."""
        if shutil.which("dar") is None:
            print("Error: DAR command ('dar') not found.", file=sys.stderr)
            print("Please ensure DAR is installed and in your PATH.", file=sys.stderr)
            return False
        print("DAR command found.")
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

    def perform_unpack(self, cleanup=False, confirm=False):
        """Download archives from S3 and unpack to destination folder."""
        # --- Initialize Checkpoint ---
        # Initialize checkpoint file if not provided
        if not self.checkpoint_file:
            # Extract folder name from source path
            folder_name = os.path.basename(os.path.normpath(self.SOURCE_PATH))
            
            # Generate checkpoint file in BASE_DOWNLOAD_PATH
            checkpoint_dir = os.path.join(self.BASE_DOWNLOAD_PATH, ".checkpoints")
            os.makedirs(checkpoint_dir, exist_ok=True)
            self.checkpoint_file = os.path.join(
                checkpoint_dir, 
                f"unpack_{folder_name}.json"
            )
            print(f"Using auto-generated checkpoint file: {self.checkpoint_file}")
        
        # Initialize checkpoint manager now that we have the filename
        self.checkpoint_manager = CheckpointManager(self.checkpoint_file)
        
        # Initialize checkpoint if needed
        if not self.resume or not self.checkpoint_manager or not self.checkpoint_manager.get_backup_id():
            # Initialize checkpoint with configuration
            config = {
                "destination_folder": self.DESTINATION_FOLDER,
                "source_profile": self.SOURCE_PROFILE,
                "source_bucket": self.SOURCE_BUCKET,
                "source_path": self.SOURCE_PATH,
                "cleanup": cleanup
            }
            self.checkpoint_manager.initialize(config)
        else:
            print(f"Resuming unpack operation with ID: {self.checkpoint_manager.get_backup_id()}")
        
        # --- Construct Paths ---
        # Download directory
        download_dir = os.path.join(self.BASE_DOWNLOAD_PATH, self.SOURCE_BUCKET, self.SOURCE_PATH)
        
        # Source S3 path
        source_s3_path = f"s3://{self.SOURCE_BUCKET}/{self.SOURCE_PATH}/"
        
        # --- Pre-run Checks ---
        print("--- Performing Pre-run Checks ---")
        if not self.check_dar_cli():
            return False
        if not self.check_aws_cli():
            return False
        if not self.check_profile_exists(self.SOURCE_PROFILE):
            return False
        print("--- Pre-run Checks Passed ---")
        
        # --- Main Unpack Process ---
        print("==================================================")
        print(f"Starting Unpack Operation")
        print(f"  Source Profile:      {self.SOURCE_PROFILE or 'Default'}")
        print(f"  Source Path:         {source_s3_path}")
        print(f"  Download Directory:  {download_dir}")
        print(f"  Destination Folder:  {self.DESTINATION_FOLDER}")
        print(f"  Cleanup Downloads:   {cleanup}")
        print(f"  Confirm Each Step:   {confirm}")
        print("==================================================")
        
        # 1. Create download directory
        print("[Step 1/3] Creating download directory...")
        
        if confirm and not self._confirm_step("create download directory", f"mkdir -p {download_dir}"):
            print("Unpack operation aborted by user.")
            return False
            
        try:
            os.makedirs(download_dir, exist_ok=True)
            print(f"         Directory created: {download_dir}")
        except OSError as e:
            print(f"Error creating directory {download_dir}: {e}", file=sys.stderr)
            return False
        
        # 2. Download archives from S3
        print("[Step 2/3] Downloading archives from S3...")
        
        # Skip download if already completed in a previous run
        if self.resume and self.checkpoint_manager and self.checkpoint_manager.is_download_complete():
            print("         Skipping download step (already completed in previous run)")
        else:
            # Download archives from S3
            download_cmd = ["aws", "s3", "sync", source_s3_path, download_dir]
            if self.SOURCE_PROFILE:
                download_cmd.extend(["--profile", self.SOURCE_PROFILE])
                
            if confirm and not self._confirm_step("download archives from S3", " ".join(download_cmd)):
                print("Unpack operation aborted by user.")
                return False
            
            if not self.run_command(download_cmd, "S3 download"):
                print("Aborting due to download error.", file=sys.stderr)
                return False
                
            # Mark download as complete
            if self.checkpoint_manager:
                # Get list of downloaded files for tracking
                downloaded_files = []
                for file in os.listdir(download_dir):
                    if file.endswith(".dar"):
                        downloaded_files.append(file)
                self.checkpoint_manager.mark_download_complete(downloaded_files)
        
        # 3. Extract archives
        print("[Step 3/3] Extracting archives to destination folder...")
        
        # Skip extraction if already completed in a previous run
        if self.resume and self.checkpoint_manager and hasattr(self.checkpoint_manager.checkpoint_data["progress"], "extraction_complete") and self.checkpoint_manager.checkpoint_data["progress"]["extraction_complete"]:
            print("         Skipping extraction step (already completed in previous run)")
        else:
            # Create destination folder if it doesn't exist
            os.makedirs(self.DESTINATION_FOLDER, exist_ok=True)
            
            # Find the first archive file to determine base name
            archive_files = [f for f in os.listdir(download_dir) if f.endswith(".1.dar")]
            if not archive_files:
                print("Error: No DAR archive files found in download directory.", file=sys.stderr)
                return False
            
            # Extract basename from first archive file (remove ".1.dar" suffix)
            archive_file = archive_files[0]
            archive_basename = archive_file[:-6]  # Remove ".1.dar"
            archive_path = os.path.join(download_dir, archive_basename)
            
            # Extract archives using dar
            dar_cmd = ["dar", "-x", archive_path, "-R", self.DESTINATION_FOLDER, "-v"]
            
            if confirm and not self._confirm_step("extract archives", " ".join(dar_cmd)):
                print("Unpack operation aborted by user.")
                return False
            
            if not self.run_command(dar_cmd, "Extracting archives"):
                print("Aborting due to extraction error.", file=sys.stderr)
                return False
                
            # Mark extraction as complete
            if self.checkpoint_manager:
                self.checkpoint_manager.checkpoint_data["progress"]["extraction_complete"] = True
                self.checkpoint_manager.save()
        
        # 4. Optional Cleanup
        if cleanup:
            print("[Cleanup] Removing downloaded archive files...")
            
            if confirm and not self._confirm_step("remove downloaded archive files", f"rm -rf {download_dir}"):
                print("Download cleanup skipped by user.")
            else:
                try:
                    shutil.rmtree(download_dir)
                    print(f"         Removed: {download_dir}")
                    print("         Cleanup complete.")
                except OSError as e:
                    print(f"Warning: Could not remove download directory {download_dir}: {e}", file=sys.stderr)
        
        print("==================================================")
        print(f"Unpack operation completed successfully")
        print(f"Files extracted to: {self.DESTINATION_FOLDER}")
        print("==================================================")
        return True