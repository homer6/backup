# Clearing Staging Directories

The `clear_staging.py` script allows you to safely delete staging directories when needed.

## Usage

```
python clear_staging.py [--folder FOLDER | --all] [options]
```

### Options

- `--folder FOLDER`: Clear a specific folder's staging directory
- `--all`: Clear all staging directories
- `--force`: Skip confirmation prompts
- `--source-profile`: AWS profile for source bucket 
- `--source-bucket`: Source S3 bucket name
- `--staging-path`: Override default staging path

## Examples

Clear a specific folder's staging directory:

```bash
python clear_staging.py --folder my-folder
```

Clear all staging directories:

```bash
python clear_staging.py --all
```