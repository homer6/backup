# Checkpoint Schema Reference

This document describes the schema and functionality of checkpoint files used in the backup system to enable resumable backups.

## Overview

Checkpoint files are JSON files that track the progress of backup operations. They allow backups to be resumed from the point of interruption, which is especially useful for large datasets or unreliable network conditions.

## File Format

Checkpoint files are stored as JSON with the following structure:

```json
{
  "backup_id": "unique-identifier",
  "source_bucket": "source-bucket-name",
  "source_path": "path/within/bucket",
  "dest_bucket": "destination-bucket-name",
  "start_time": "2024-04-06T12:00:00",
  "last_update": "2024-04-06T13:15:30",
  "total_files": 1250,
  "processed_files": 820,
  "total_bytes": 1073741824,
  "processed_bytes": 536870912,
  "files": {
    "path/to/file1.txt": true,
    "path/to/file2.dat": true,
    "path/to/file3.csv": false
  },
  "errors": {
    "path/to/problem_file.bin": "AccessDenied: Access Denied"
  },
  "config": {
    "cleanup": true,
    "base_local_path": "/path/to/local/storage"
  }
}
```

## Fields

| Field | Type | Description |
|-------|------|-------------|
| `backup_id` | String | Unique identifier for the backup job |
| `source_bucket` | String | Name of the S3 source bucket |
| `source_path` | String | Path prefix within the source bucket |
| `dest_bucket` | String | Name of the S3 destination bucket |
| `start_time` | ISO DateTime | When the backup job was first started |
| `last_update` | ISO DateTime | When the checkpoint was last updated |
| `total_files` | Integer | Total number of files to backup |
| `processed_files` | Integer | Number of files processed so far |
| `total_bytes` | Integer | Total size of all files in bytes |
| `processed_bytes` | Integer | Size of processed files in bytes |
| `files` | Object | Map of file paths to boolean values indicating completion |
| `errors` | Object | Map of file paths to error messages |
| `config` | Object | Backup configuration parameters |

## File Status Values

In the `files` object, each file path maps to a boolean:

- `true`: The file has been successfully processed
- `false`: The file has not been processed yet or failed to process

## How Checkpoints Work

1. **Initialization**: When a backup starts, it checks if a checkpoint file exists
   - If no checkpoint exists, a new one is created
   - If a checkpoint exists, it's loaded to resume the backup

2. **During Backup**: After each file is processed:
   - The checkpoint file is updated to mark the file as processed
   - Counters for processed files and bytes are updated
   - The `last_update` timestamp is refreshed

3. **On Completion**: When the backup finishes successfully:
   - The checkpoint file is either deleted or archived
   - A completion log entry is made

4. **On Failure**: If the backup is interrupted:
   - The checkpoint file remains in place
   - The next backup run will use it to resume operations

## Checkpoint File Naming and Location

By default, checkpoint files are stored in the local staging directory with a naming convention:

```
<base_local_path>/checkpoints/<source_bucket>_<source_path>.checkpoint
```

The `source_path` portion of the filename is sanitized to replace invalid characters with underscores.

## Example Usage

### Resuming from checkpoint

```bash
# Initial run (interrupted after 820 of 1250 files)
python backup_s3.py Projects/TeamA/2024Q1 --dest-profile prod --source-bucket company-data-db --dest-bucket company-archive --cleanup --base-local-path /mnt/data/scratch

# Later run (will resume from file 821)
python backup_s3.py Projects/TeamA/2024Q1 --dest-profile prod --source-bucket company-data-db --dest-bucket company-archive --cleanup --base-local-path /mnt/data/scratch
```

### Ignoring checkpoints

To force a backup to start from the beginning regardless of existing checkpoints:

```bash
python backup_s3.py Projects/TeamA/2024Q1 --dest-profile prod --source-bucket company-data-db --dest-bucket company-archive --cleanup --base-local-path /mnt/data/scratch --ignore-checkpoints
```

### Custom checkpoint directory

```bash
python backup_s3.py Projects/TeamA/2024Q1 --dest-profile prod --source-bucket company-data-db --dest-bucket company-archive --cleanup --base-local-path /mnt/data/scratch --checkpoint-dir /persistent/storage/checkpoints
```

## Advanced Features

### Checkpoint Frequency

By default, the checkpoint file is updated after each file is processed. For very large datasets with small files, this can create I/O overhead. The checkpoint frequency can be adjusted:

```bash
python backup_s3.py BigDataset --dest-profile prod --source-bucket company-data-db --dest-bucket company-archive --cleanup --base-local-path /mnt/data/scratch --checkpoint-interval 100
```

This updates the checkpoint file after every 100 files are processed.

### Manual Checkpoint Manipulation

In rare cases, you might need to manually edit a checkpoint file to:

1. Skip problematic files by marking them as `true` in the `files` object
2. Reset progress for specific files by changing their status to `false`
3. Clear errors by removing entries from the `errors` object

Example of manually manipulating a checkpoint:

```bash
# Edit the checkpoint file
vi /mnt/data/scratch/checkpoints/company-data-db_Projects_TeamA_2024Q1.checkpoint

# Change the status of a problematic file
# "path/to/problem_file.dat": false → "path/to/problem_file.dat": true
```

## Troubleshooting

### Common Issues

1. **Checkpoint not found**: Ensure the `base_local_path` matches between runs
2. **Checkpoint not updating**: Check for file system permissions or disk space issues
3. **Resuming at wrong point**: Verify the checkpoint file contents for corruption

### Checkpoint Verification

You can check the status of a checkpoint file using:

```bash
cat /path/to/checkpoint/file.checkpoint | jq
```

This displays the formatted JSON content of the checkpoint file (requires the `jq` utility).

## Implementation Details

The checkpoint system is implemented in the `backup_utils/checkpoint.py` module, which provides:

- `CheckpointManager` class for creating, loading, and updating checkpoints
- Helper functions for checkpoint file path resolution
- Error handling for checkpoint file operations

The actual backup tools (`backup_s3.py` and `backup_github.py`) integrate with this module to provide resumable backup functionality.