# GitHub Backup Tool

A Python utility for backing up all repositories from a GitHub organization, with options to include wikis and LFS objects, create archives, and upload to S3.

## Usage

Backup all repositories in a GitHub organization. The GitHub token must be provided through the environment variable `GITHUB_TOKEN`.

```
python backup_github.py <org_name> [options]
```

### Arguments

- `org_name`: GitHub organization name to backup.

### Options

- `--local-path`: Base directory on local machine for repository backups (default: ~/github_backup_staging)
- `--include-forks`: Include forked repositories in the backup
- `--include-wikis`: Download wiki pages for each repository
- `--include-lfs`: Include Git LFS objects in the clones
- `--cleanup`: Remove local repositories after successful backup
- `--confirm`: Confirm each step before execution
- `--create-archives`: Create archives of each repository
- `--volume-size`: Size limit for each archive volume (default: 1G)
- `--upload-to-s3`: Upload archives to S3 bucket
- `--s3-profile`: AWS profile for S3 upload
- `--s3-bucket`: Destination S3 bucket name
- `--s3-path`: Destination path within the bucket (default: github_backups/<org_name>)
- `--storage-class`: Storage class for S3 objects (default: "DEEP_ARCHIVE")
- `--checkpoint-file`: Path to checkpoint file to save progress
- `--no-resume`: Don't resume from previous checkpoint, even if one exists

## Examples

First, set your GitHub token as an environment variable:

```bash
export GITHUB_TOKEN=your_github_personal_access_token
```

Back up all repositories in an organization:

```bash
python backup_github.py my-org-name
```

Back up all repositories including wikis and LFS objects:

```bash
python backup_github.py my-org-name --include-wikis --include-lfs
```

Back up all repositories, create archives, and upload to S3:

```bash
python backup_github.py my-org-name --create-archives --upload-to-s3 --s3-bucket my-backup-bucket
```

Back up all repositories with confirmation at each step:

```bash
python backup_github.py my-org-name --confirm
```

Resume a previously interrupted backup:

```bash
python backup_github.py my-org-name
```

## Process

1. Fetch the list of repositories for the specified organization
2. Clone each repository (with optional wiki and LFS objects)
3. Optionally create archives of each repository using DAR
4. Optionally upload the archives to S3 with timestamp
5. Optionally clean up local repositories and archive directories