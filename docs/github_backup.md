# GitHub Backup Tool

A Python utility for backing up all repositories from a GitHub organization. By default, it creates DAR archives and uploads them to S3 with automatic bucket naming.

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
- `--no-archives`: Skip creating DAR archives of each repository (optional, default: false)
- `--no-s3-upload`: Skip uploading archives to S3 bucket (optional, default: false)
- `--dest-bucket`: Destination S3 bucket name (optional, default: <org-name>-github-backups)
- `--dest-profile`: AWS profile for S3 upload (optional, default: uses default profile)
- `--dest-s3-path`: Destination path within the bucket (optional, default: github_backups/<org_name>)
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

Back up all repositories in an organization (with DAR archiving and S3 upload by default):

```bash
python backup_github.py my-org-name
```

Back up all repositories including wikis and LFS objects:

```bash
python backup_github.py my-org-name --include-wikis --include-lfs
```

Back up all repositories without creating archives or uploading to S3:

```bash
python backup_github.py my-org-name --no-archives --no-s3-upload
```

Back up all repositories with a custom S3 bucket name:

```bash
python backup_github.py my-org-name --dest-bucket custom-bucket-name
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
3. Create DAR archives of each repository (disabled with --no-archives)
4. Upload the archives to S3 with timestamp (disabled with --no-s3-upload)
5. Optionally clean up local repositories and archive directories