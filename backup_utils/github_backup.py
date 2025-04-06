import os
import subprocess
import sys
import shutil
import datetime
import glob
import requests
import json
from backup_utils.checkpoint import CheckpointManager

class GitHubBackup:
    def __init__(self, org_name, github_token, base_local_path=None,
                include_forks=False, include_wikis=False, include_lfs=False,
                s3_profile="", s3_bucket="", s3_path="",
                storage_class="DEEP_ARCHIVE",
                checkpoint_file=None, resume=True):
        # --- Configuration ---
        self.ORG_NAME = org_name
        self.GITHUB_TOKEN = github_token
        
        # Base directory on your local machine for repository backups
        self.BASE_LOCAL_PATH = base_local_path or os.path.expanduser("~/github_backup_staging")
        
        # Backup options
        self.INCLUDE_FORKS = include_forks
        self.INCLUDE_WIKIS = include_wikis
        self.INCLUDE_LFS = include_lfs
        
        # S3 Upload Settings
        self.S3_PROFILE = s3_profile
        self.S3_BUCKET = s3_bucket
        self.S3_PATH = s3_path or f"github_backups/{org_name}"
        
        # S3 storage class for destination bucket
        self.STORAGE_CLASS = storage_class
        
        # Checkpointing
        self.resume = resume
        self.checkpoint_manager = None
        self.checkpoint_file = checkpoint_file
        # We'll initialize the checkpoint manager when we have the folder to backup
        
        # GitHub API base URL
        self.GITHUB_API_BASE = "https://api.github.com"

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

    def check_git_cli(self):
        """Checks if the Git CLI command is available."""
        if shutil.which("git") is None:
            print("Error: Git CLI command ('git') not found.", file=sys.stderr)
            print("Please ensure Git is installed and in your PATH.", file=sys.stderr)
            return False
        print("Git CLI found.")
        return True

    def check_aws_cli(self):
        """Checks if the AWS CLI command is available."""
        if self.S3_BUCKET and shutil.which("aws") is None:
            print("Error: AWS CLI command ('aws') not found.", file=sys.stderr)
            print("Please ensure the AWS CLI v2 is installed and in your PATH.", file=sys.stderr)
            return False
        if self.S3_BUCKET:
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

    def check_s3_profile(self):
        """Checks if a named profile exists in standard AWS config/credentials files."""
        if not self.S3_PROFILE or not self.S3_BUCKET:  # Don't check if profile name is blank (use default)
            return True

        import configparser
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
        profile_section_config = f"profile {self.S3_PROFILE}"
        profile_section_creds = self.S3_PROFILE

        if (config_exists and profile_section_config in config) or \
           (creds_exists and profile_section_creds in creds):
            print(f"AWS profile '{self.S3_PROFILE}' found.")
            return True
        else:
            print(f"Error: AWS profile '{self.S3_PROFILE}' not found in {config_path} or {creds_path}.", file=sys.stderr)
            print(f"Please configure it using: aws configure --profile {self.S3_PROFILE}", file=sys.stderr)
            return False

    def get_repositories(self):
        """Gets a list of repositories for the organization using GitHub API."""
        headers = {
            'Accept': 'application/vnd.github+json',
            'Authorization': f'Bearer {self.GITHUB_TOKEN}',
            'X-GitHub-Api-Version': '2022-11-28'
        }

        page = 1
        repos = []
        while True:
            url = f"{self.GITHUB_API_BASE}/orgs/{self.ORG_NAME}/repos?per_page=100&page={page}"
            try:
                response = requests.get(url, headers=headers)
                response.raise_for_status()  # Raise an error for bad responses (4xx or 5xx)
                
                page_repos = response.json()
                if not page_repos:  # No more repositories
                    break
                    
                repos.extend(page_repos)
                page += 1
            except requests.exceptions.RequestException as e:
                print(f"Error fetching repositories: {e}", file=sys.stderr)
                if hasattr(e, 'response') and e.response:
                    print(f"Response status code: {e.response.status_code}", file=sys.stderr)
                    print(f"Response content: {e.response.text}", file=sys.stderr)
                return None
        
        # Filter out forks if needed
        if not self.INCLUDE_FORKS:
            repos = [repo for repo in repos if not repo['fork']]
            
        return repos

    def clone_repository(self, repo_name, clone_url, backup_dir, include_lfs=False, include_wiki=False):
        """Clone a GitHub repository."""
        repo_dir = os.path.join(backup_dir, repo_name)
        
        # Skip if already cloned and we're resuming
        if os.path.exists(repo_dir) and os.path.isdir(os.path.join(repo_dir, '.git')):
            if self.resume:
                print(f"Repository {repo_name} already cloned, updating...")
                # Update the repository
                update_cmd = ["git", "-C", repo_dir, "fetch", "--all", "--tags", "--prune"]
                if not self.run_command(update_cmd, f"updating repository {repo_name}"):
                    return False
                return True
            else:
                # Remove existing directory if not resuming
                try:
                    shutil.rmtree(repo_dir)
                except OSError as e:
                    print(f"Error removing directory {repo_dir}: {e}", file=sys.stderr)
                    return False
        
        # Clone with authentication via HTTPS
        auth_url = clone_url.replace("https://", f"https://x-access-token:{self.GITHUB_TOKEN}@")
        
        # Prepare the clone command
        clone_cmd = ["git", "clone", "--mirror", auth_url, repo_dir]
        
        # Clone the repository
        if not self.run_command(clone_cmd, f"cloning repository {repo_name}"):
            return False
            
        # Setup LFS if needed
        if include_lfs:
            lfs_cmd = ["git", "-C", repo_dir, "lfs", "fetch", "--all"]
            if not self.run_command(lfs_cmd, f"fetching LFS objects for {repo_name}"):
                print(f"Warning: Failed to fetch LFS objects for {repo_name}", file=sys.stderr)
        
        # Clone wiki if needed
        if include_wiki:
            wiki_url = clone_url.replace(".git", ".wiki.git")
            wiki_auth_url = wiki_url.replace("https://", f"https://x-access-token:{self.GITHUB_TOKEN}@")
            wiki_dir = os.path.join(backup_dir, f"{repo_name}.wiki")
            
            wiki_cmd = ["git", "clone", "--mirror", wiki_auth_url, wiki_dir]
            # Don't fail the whole backup if wiki clone fails (wiki might not exist)
            if not self.run_command(wiki_cmd, f"cloning wiki for {repo_name}"):
                print(f"Note: No wiki found for {repo_name} or failed to clone it.", file=sys.stderr)
        
        return True

    def create_archive(self, repo_name, backup_dir, archive_dir, volume_size="1G"):
        """Create a DAR archive of a repository."""
        repo_dir = os.path.join(backup_dir, repo_name)
        
        # Create the archive directory if it doesn't exist
        try:
            os.makedirs(archive_dir, exist_ok=True)
        except OSError as e:
            print(f"Error creating archive directory {archive_dir}: {e}", file=sys.stderr)
            return False
        
        # Create the archive with DAR
        archive_basename = os.path.join(archive_dir, repo_name)
        dar_cmd = ["dar", "-w", "-s", volume_size, "-c", archive_basename, "-R", repo_dir]
        
        return self.run_command(dar_cmd, f"creating archive for {repo_name}")

    def upload_to_s3(self, repo_name, archive_dir, dest_s3_path):
        """Upload the repository archive to S3."""
        if not self.S3_BUCKET:
            print(f"Skipping S3 upload for {repo_name} (no S3 bucket specified)")
            return True
            
        # Construct the S3 destination path
        repo_s3_path = f"{dest_s3_path}/{repo_name}/"
        
        # Prepare the S3 upload command
        upload_cmd = ["aws", "s3", "sync", archive_dir, repo_s3_path, "--storage-class", self.STORAGE_CLASS]
        if self.S3_PROFILE:
            upload_cmd.extend(["--profile", self.S3_PROFILE])
            
        return self.run_command(upload_cmd, f"uploading {repo_name} to S3")

    def perform_backup(self, create_archives=False, upload_to_s3=False, cleanup=False, confirm=False, volume_size="1G"):
        """Perform the GitHub repositories backup process."""
        # Generate timestamp for this backup
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Initialize checkpoint file if not provided
        if not self.checkpoint_file:
            # Generate checkpoint file in BASE_LOCAL_PATH
            checkpoint_dir = os.path.join(self.BASE_LOCAL_PATH, ".checkpoints")
            os.makedirs(checkpoint_dir, exist_ok=True)
            self.checkpoint_file = os.path.join(
                checkpoint_dir, 
                f"{self.ORG_NAME}_github_backup.json"
            )
            print(f"Using auto-generated checkpoint file: {self.checkpoint_file}")
        
        # Initialize checkpoint manager now that we have the filename
        self.checkpoint_manager = CheckpointManager(self.checkpoint_file)
        
        # Use existing backup ID from checkpoint or create new one
        if self.resume and self.checkpoint_manager and self.checkpoint_manager.get_backup_id():
            timestamp = self.checkpoint_manager.get_backup_id()
            print(f"Resuming backup with ID: {timestamp}")
        else:
            # Initialize checkpoint with configuration
            config = {
                "org_name": self.ORG_NAME,
                "include_forks": self.INCLUDE_FORKS,
                "include_wikis": self.INCLUDE_WIKIS,
                "include_lfs": self.INCLUDE_LFS,
                "s3_profile": self.S3_PROFILE,
                "s3_bucket": self.S3_BUCKET,
                "s3_path": self.S3_PATH,
                "create_archives": create_archives,
                "upload_to_s3": upload_to_s3,
                "cleanup": cleanup,
                "volume_size": volume_size
            }
            self.checkpoint_manager.initialize(config)
        
        # --- Directories setup ---
        # Main backup directory for repositories
        backup_dir = os.path.join(self.BASE_LOCAL_PATH, self.ORG_NAME, timestamp, "repositories")
        
        # Archive directory if creating archives
        archive_dir = os.path.join(self.BASE_LOCAL_PATH, self.ORG_NAME, timestamp, "archives")
        
        # Construct S3 destination path if uploading to S3
        dest_s3_path = f"s3://{self.S3_BUCKET}/{self.S3_PATH}/{timestamp}"
        
        # --- Pre-run Checks ---
        print("--- Performing Pre-run Checks ---")
        if not self.check_git_cli():
            return False
        if create_archives and not self.check_dar_cli():
            return False
        if upload_to_s3:
            if not self.check_aws_cli():
                return False
            if not self.check_s3_profile():
                return False
        print("--- Pre-run Checks Passed ---")
        
        # --- Main Backup Process ---
        print("==================================================")
        print(f"Starting GitHub Backup for organization: {self.ORG_NAME}")
        print(f"  Include Forks:         {self.INCLUDE_FORKS}")
        print(f"  Include Wikis:         {self.INCLUDE_WIKIS}")
        print(f"  Include LFS Objects:   {self.INCLUDE_LFS}")
        print(f"  Create Archives:       {create_archives}")
        print(f"  Upload to S3:          {upload_to_s3}")
        if upload_to_s3:
            print(f"  S3 Profile:           {self.S3_PROFILE or 'Default'}")
            print(f"  S3 Bucket:            {self.S3_BUCKET}")
            print(f"  S3 Path:              {dest_s3_path}")
            print(f"  Storage Class:        {self.STORAGE_CLASS}")
        print(f"  Local Backup Dir:      {backup_dir}")
        print(f"  Cleanup Local Dir:     {cleanup}")
        print(f"  Confirm Each Step:     {confirm}")
        print("==================================================")
        
        # 1. Get repositories list
        print("[Step 1] Fetching repositories list...")
        
        # Skip fetching if already completed in a previous run
        if self.resume and self.checkpoint_manager and hasattr(self.checkpoint_manager, 'checkpoint_data') and 'repositories' in self.checkpoint_manager.checkpoint_data:
            print("         Using repository list from checkpoint")
            repos = self.checkpoint_manager.checkpoint_data['repositories']
        else:
            if confirm and not self._confirm_step("fetch repositories list"):
                print("Backup aborted by user.")
                return False
            
            repos = self.get_repositories()
            if repos is None:
                print("Aborting due to repository list fetch error.", file=sys.stderr)
                return False
            
            # Store repositories in checkpoint
            if self.checkpoint_manager:
                self.checkpoint_manager.checkpoint_data['repositories'] = repos
                self.checkpoint_manager.save()
        
        print(f"         Found {len(repos)} repositories")
        
        # 2. Create backup directory
        print("[Step 2] Creating backup directories...")
        
        if confirm and not self._confirm_step("create backup directories"):
            print("Backup aborted by user.")
            return False
        
        try:
            os.makedirs(backup_dir, exist_ok=True)
            print(f"         Directory created: {backup_dir}")
            if create_archives:
                os.makedirs(archive_dir, exist_ok=True)
                print(f"         Directory created: {archive_dir}")
        except OSError as e:
            print(f"Error creating directories: {e}", file=sys.stderr)
            return False
        
        # 3. Clone repositories
        print("[Step 3] Cloning repositories...")
        
        # Get previously completed repositories from checkpoint
        completed_repos = []
        if self.resume and self.checkpoint_manager and 'completed_repos' in self.checkpoint_manager.checkpoint_data:
            completed_repos = self.checkpoint_manager.checkpoint_data['completed_repos']
        
        # Process each repository
        success_count = 0
        for repo in repos:
            repo_name = repo['name']
            clone_url = repo['clone_url']
            
            # Skip if already completed in a previous run
            if repo_name in completed_repos and self.resume:
                print(f"         Repository {repo_name} already processed in previous run, skipping...")
                success_count += 1
                continue
            
            print(f"Processing repository: {repo_name}")
            
            if confirm and not self._confirm_step(f"clone repository {repo_name}"):
                print(f"Skipping repository {repo_name} as requested by user.")
                continue
            
            # Clone the repository
            if not self.clone_repository(
                repo_name, 
                clone_url, 
                backup_dir, 
                include_lfs=self.INCLUDE_LFS, 
                include_wiki=self.INCLUDE_WIKIS
            ):
                print(f"Error cloning repository {repo_name}. Continuing with next repository.", file=sys.stderr)
                continue
            
            # Create archive if requested
            if create_archives:
                if confirm and not self._confirm_step(f"create archive for {repo_name}"):
                    print(f"Skipping archive creation for {repo_name} as requested by user.")
                else:
                    repo_archive_dir = os.path.join(archive_dir, repo_name)
                    if not self.create_archive(repo_name, backup_dir, repo_archive_dir, volume_size):
                        print(f"Error creating archive for {repo_name}. Continuing with next repository.", file=sys.stderr)
                        continue
            
            # Upload to S3 if requested
            if upload_to_s3 and create_archives:
                if confirm and not self._confirm_step(f"upload {repo_name} to S3"):
                    print(f"Skipping S3 upload for {repo_name} as requested by user.")
                else:
                    repo_archive_dir = os.path.join(archive_dir, repo_name)
                    repo_s3_path = f"{dest_s3_path}/{repo_name}"
                    if not self.upload_to_s3(repo_name, repo_archive_dir, repo_s3_path):
                        print(f"Error uploading {repo_name} to S3. Continuing with next repository.", file=sys.stderr)
                        continue
            
            # Mark repository as completed
            if self.checkpoint_manager:
                if 'completed_repos' not in self.checkpoint_manager.checkpoint_data:
                    self.checkpoint_manager.checkpoint_data['completed_repos'] = []
                self.checkpoint_manager.checkpoint_data['completed_repos'].append(repo_name)
                self.checkpoint_manager.save()
            
            success_count += 1
        
        # 4. Cleanup if requested
        if cleanup:
            print("[Step 4] Cleaning up local directories...")
            
            if confirm and not self._confirm_step("cleanup local directories"):
                print("Cleanup skipped as requested by user.")
            else:
                try:
                    shutil.rmtree(backup_dir)
                    print(f"         Removed: {backup_dir}")
                    if create_archives:
                        shutil.rmtree(archive_dir)
                        print(f"         Removed: {archive_dir}")
                    print("         Cleanup complete.")
                except OSError as e:
                    print(f"Warning: Could not remove local directories: {e}", file=sys.stderr)
        
        print("==================================================")
        print(f"Backup process completed. Successfully processed {success_count} out of {len(repos)} repositories.")
        print("==================================================")
        
        return success_count > 0