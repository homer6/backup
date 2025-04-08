# Backup Tools

This repository contains utility scripts for backing up data from various sources.

## Available Tools

- [S3 Backup Tool](docs/s3_backup.md): Back up data from one S3 bucket to another, with archiving and timestamping
- [GitHub Backup Tool](docs/github_backup.md): Back up all repositories from a GitHub organization
- [Pack Tool](docs/pack.md): Pack a folder into DAR archives and upload to S3
- [Unpack Tool](docs/unpack.md): Download archives from S3 and unpack them to a folder
- [Clear Staging Tool](docs/clear_staging.md): Safely delete staging directories

## Common Documentation

- [Installation and Setup](docs/common.md): Prerequisites, Python environment setup, and code structure
- [Resumable Backups](docs/resumable_backups.md): How the checkpoint system works
- [AWS Sync Settings](docs/common.md#recommended-aws-sync-settings): Recommended AWS configuration settings

## Quick Start

### S3 Backup

```bash
python backup_s3.py [folder_name] --confirm
```

### GitHub Backup

```bash
export GITHUB_TOKEN=your_github_personal_access_token
python backup_github.py <org_name> --confirm
```

By default, this creates DAR archives and uploads them to S3 with bucket name `<org-name>-github-backups`.

### Pack a Folder

```bash
python pack.py /path/to/folder --dest-bucket my-backups --confirm
```

### Unpack Archives

```bash
python unpack.py /path/to/destination --s3-path s3://my-backups/packed_folders/folder_name/20250407_120000 --confirm
```

### Clear Staging Directories

```bash
python clear_staging.py --folder <folder_name>
```

See the documentation in the [docs](docs/) directory for detailed usage information.