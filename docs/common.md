# Common Setup and Configuration

## Installation

### Prerequisites

Ensure you have the following:

- Python 3.6+
- AWS CLI v2 (required for S3 operations)
- Git CLI (required for GitHub backup)
- DAR (Disk ARchive) utility installed
  - Ubuntu/Debian: `sudo apt install dar`
  - macOS: `brew install dar`
- Properly configured AWS credentials (for S3 operations)
- GitHub personal access token with `repo` scope (for GitHub backup, set as environment variable `GITHUB_TOKEN`)

### Setting Up a Python Environment

1. Clone the repository:
   ```bash
   git clone https://github.com/your-username/backup.git
   cd backup
   ```

2. Create a virtual environment:
   ```bash
   # Using venv (Python's built-in module)
   python3 -m venv venv
   
   # Activate the virtual environment
   # On macOS/Linux:
   source venv/bin/activate
   # On Windows:
   venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up the GitHub token (if using GitHub backup):
   ```bash
   # Create a personal access token at https://github.com/settings/tokens
   # Make sure it has 'repo' scope permissions
   export GITHUB_TOKEN=your_github_personal_access_token
   ```

## Recommended AWS Sync Settings

These settings can improve the performance of AWS S3 operations:

```bash
aws configure set default.s3.max_concurrent_requests 64
aws configure set default.s3.max_queue_size 10000
aws configure get default.s3.multipart_threshold
aws configure set default.s3.multipart_threshold 100MB
aws configure set default.s3.multipart_chunksize 100MB
```

## Code Structure

- `backup_s3.py`: Main script for executing S3 backups
- `backup_github.py`: Main script for executing GitHub organization backups
- `backup_utils/s3_backup.py`: Core S3Backup class with S3 backup functionality
- `backup_utils/github_backup.py`: Core GitHubBackup class with GitHub backup functionality
- `backup_utils/checkpoint.py`: Handles checkpoint management for resumable backups
- `clear_staging.py`: Script for managing staging directories