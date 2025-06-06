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

## Command-Line Options

- `--checkpoint-dir`: Specify a custom directory for checkpoint files
- `--ignore-checkpoints`: Force backup to start from beginning, ignoring checkpoints
- `--checkpoint-interval`: Control how frequently checkpoint files are updated

## Working with Nested Folders

The checkpoint system works seamlessly with nested folder structures:

```bash
# Backing up a nested folder structure
python backup_s3.py Projects/TeamA/2024Q1 --dest-profile prod --source-bucket company-data --dest-bucket archive --cleanup --base-local-path /mnt/data

# If interrupted, running the same command will resume where it left off
```

Checkpoint files for nested paths use a naming convention that replaces slashes with underscores.

## Example Workflow

1. Start a backup: `python backup_s3.py my-folder` or `python backup_github.py my-org-name`
2. If the process is interrupted, run the same command again
3. The script will automatically detect the previous progress and resume from the last completed step

## Checkpoint Files

Checkpoint files are stored in JSON format and contain:
- List of processed files
- Backup configuration details
- Progress statistics

For detailed information about the schema and structure of checkpoint files, see the [Checkpoint Schema Reference](checkpoint_schema.md).

## Best Practices

- Use consistent command-line arguments between runs
- For very large backups, consider breaking them into smaller logical chunks
- Set an appropriate checkpoint interval for your dataset size
- Store checkpoint files on reliable, persistent storage with the `--checkpoint-dir` option

## Troubleshooting

If a backup is not resuming correctly:
1. Check if checkpoint files exist in the expected location
2. Verify the checkpoint file integrity
3. Consider using --ignore-checkpoints to start fresh

For more advanced troubleshooting and examples, see the [Examples Directory](../examples/resumable_backup_examples.md).