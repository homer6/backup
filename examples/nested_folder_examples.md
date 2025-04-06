# Nested Folder Backup Examples

This document provides examples specifically focused on backing up nested folder structures in S3 and GitHub.

## S3 Nested Folder Backups

### Example 1: Basic Nested Folder Backup
```bash
python backup_s3.py Projects/TeamA/2024Q1 --dest-profile prod --source-bucket company-data-db --dest-bucket company-archive --cleanup --base-local-path /mnt/data/scratch
```
This backs up a specific nested folder path (Projects/TeamA/2024Q1) from the company-data-db bucket. The nested folder structure is preserved in the destination bucket.

### Example 2: Backing Up Multiple Nested Folders
```bash
# Back up multiple nested folders in sequence
python backup_s3.py Projects/TeamA/2024Q1 --dest-profile prod --source-bucket company-data-db --dest-bucket company-archive --cleanup --base-local-path /mnt/data/scratch
python backup_s3.py Projects/TeamA/2024Q2 --dest-profile prod --source-bucket company-data-db --dest-bucket company-archive --cleanup --base-local-path /mnt/data/scratch
python backup_s3.py Projects/TeamB/2024Q1 --dest-profile prod --source-bucket company-data-db --dest-bucket company-archive --cleanup --base-local-path /mnt/data/scratch
python backup_s3.py Projects/TeamB/2024Q2 --dest-profile prod --source-bucket company-data-db --dest-bucket company-archive --cleanup --base-local-path /mnt/data/scratch
```
This script backs up multiple quarterly folders for different teams, each with their own nested path.

### Example 3: Backing Up an Entire Project Folder and All Subfolders
```bash
# Back up all teams and quarters under the Projects folder
python backup_s3.py Projects --dest-profile prod --source-bucket company-data-db --dest-bucket company-archive --cleanup --base-local-path /mnt/data/scratch
```
This backs up the entire Projects folder and all subfolders, including all team and quarter folders.

## GitHub Nested Team Structure Backups

### Example 4: Backing Up Repositories in a Nested Team Structure
```bash
# Back up repositories from nested team structure
python backup_github.py company/product-team --dest-profile prod --dest-bucket github-archives --cleanup --base-local-path /mnt/data/github-backups
python backup_github.py company/engineering-team --dest-profile prod --dest-bucket github-archives --cleanup --base-local-path /mnt/data/github-backups
```
This backs up repositories from different teams within the company organization.

### Example 5: Backing Up Deeply Nested Team Repositories
```bash
# Back up repositories from more deeply nested teams
python backup_github.py company/platform-team/frontend --dest-profile prod --dest-bucket github-archives --cleanup --base-local-path /mnt/data/github-backups
python backup_github.py company/platform-team/backend --dest-profile prod --dest-bucket github-archives --cleanup --base-local-path /mnt/data/github-backups
python backup_github.py company/platform-team/infrastructure --dest-profile prod --dest-bucket github-archives --cleanup --base-local-path /mnt/data/github-backups
```
This demonstrates backing up repositories from teams that are organized in a deeper nested structure.

## Checkpoint Files for Nested Paths

### Example 6: Understanding Checkpoint File Naming for Nested Paths
```bash
# Back up nested folder path
python backup_s3.py Projects/TeamA/2024Q1 --dest-profile prod --source-bucket company-data-db --dest-bucket company-archive --cleanup --base-local-path /mnt/data/scratch
```

This creates a checkpoint file with a name like:
```
/mnt/data/scratch/checkpoints/company-data-db_Projects_TeamA_2024Q1.checkpoint
```

The checkpoint filename encodes the nested folder structure by replacing slashes with underscores.

### Example 7: Custom Checkpoint Directory with Nested Paths
```bash
python backup_s3.py Projects/TeamA/2024Q1 --dest-profile prod --source-bucket company-data-db --dest-bucket company-archive --cleanup --base-local-path /mnt/data/scratch --checkpoint-dir /persistent/storage/checkpoints
```

This creates a checkpoint file with a name like:
```
/persistent/storage/checkpoints/company-data-db_Projects_TeamA_2024Q1.checkpoint
```

## Automation for Nested Folders

### Example 8: Script to Back Up Recent Nested Folders
```bash
#!/bin/bash
# backup_recent_project_folders.sh

# Find folders modified in the last 7 days
aws s3 ls s3://company-data-db/Projects/ --recursive | grep $(date -d "7 days ago" +%Y-%m-%d) | awk '{print $4}' | grep -o "Projects/[^/]*/[^/]*" | sort | uniq > recent_folders.txt

# Back up each folder with recent changes
while read folder; do
  echo "Backing up folder with recent changes: $folder"
  python backup_s3.py $folder --dest-profile prod --source-bucket company-data-db --dest-bucket company-archive --cleanup --base-local-path /mnt/data/scratch
done < recent_folders.txt
```

This script:
1. Finds nested project folders with recent modifications
2. Extracts the project team and quarter level paths
3. Backs up each recently modified folder

### Example 9: Handling Nested Paths with Spaces or Special Characters
```bash
# Backing up a path with spaces and special characters
python backup_s3.py "Projects/Client Projects/2024 Q1 (Final)" --dest-profile prod --source-bucket company-data-db --dest-bucket company-archive --cleanup --base-local-path /mnt/data/scratch
```

Special characters in the nested path are properly handled by the backup system, and the checkpoint file will safely encode these characters in its filename.

## Best Practices for Nested Folders

1. **Consistent Path Structure**: Maintain a consistent nesting structure (e.g., Projects/Team/Quarter) to make scripts and automation easier
2. **Path Depth Consideration**: Very deep nesting (more than 4-5 levels) may impact performance and usability
3. **Checkpoint Management**: For deeply nested paths, consider using a custom checkpoint directory with shorter names
4. **Automation**: When automating backups of nested structures, always test with a small subset first