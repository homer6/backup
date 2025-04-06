# Resumable Backups

Both the S3 and GitHub backup scripts automatically use resumable backups with smart checkpoint file naming. This allows you to resume an interrupted backup process without having to restart from the beginning.

## Key Features

- Checkpoint files are automatically created based on backup configuration:
  - For S3: based on bucket and folder names, stored in `~/s3_backup_staging/.checkpoints/`
  - For GitHub: based on organization name, stored in `~/github_backup_staging/.checkpoints/`
- The scripts automatically save progress after each major step:
  - For S3 backups:
    - After download from S3 is complete
    - After archive creation is complete
    - After upload to destination S3 is complete
  - For GitHub backups:
    - After fetching repository list
    - After processing each repository
- If a backup is interrupted, simply running the same command again will resume from where it left off
- Use `--no-resume` to start a fresh backup and ignore existing checkpoint
- You can still specify a custom checkpoint file with `--checkpoint-file` if needed

## Example Workflow

1. Start a backup: `python backup_s3.py my-folder` or `python backup_github.py my-org-name`
2. If the process is interrupted, run the same command again
3. The script will automatically detect the previous progress and resume from the last completed step