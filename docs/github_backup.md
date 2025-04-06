# GitHub Backup Tool

A Python utility for backing up all repositories from a GitHub organization, with options to include wikis and LFS objects, create archives, and upload to S3.

## Usage

Backup all repositories in a GitHub organization. The GitHub token must be provided through the environment variable `GITHUB_TOKEN`.

```
python backup_github.py <org_name> [options]
```

### Arguments

- `org_name`: GitHub organization name to backup (required)
- `GITHUB_TOKEN`: Environment variable containing GitHub authentication token (required)

### Options

- `--local-path`: Base directory for repository backups (optional, default: ~/github_backup_staging)
- `--include-forks`: Include forked repositories in the backup (optional, default: false)
- `--include-wikis`: Download wiki pages for each repository (optional, default: false)
- `--include-lfs`: Include Git LFS objects in the clones (optional, default: false)
- `--create-archives`: Create archives of each repository (optional, default: false)
- `--upload-to-s3`: Upload archives to S3 bucket (optional, default: false)
- `--s3-bucket`: Destination S3 bucket name (required when --upload-to-s3 is used)
- `--s3-profile`: AWS profile for S3 upload (optional, default: uses default profile)
- `--s3-path`: Destination path within the bucket (optional, default: github_backups/<org_name>)
- `--storage-class`: Storage class for S3 objects (optional, default: "DEEP_ARCHIVE")
- `--cleanup`: Remove local repositories after successful backup (optional, default: false)
- `--confirm`: Confirm each step before execution (optional, default: false)
- `--volume-size`: Size limit for each archive volume (optional, default: "1G")
- `--checkpoint-file`: Path to checkpoint file to save progress (optional, default: auto-generated)
- `--no-resume`: Don't resume from previous checkpoint (optional, default: false)

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