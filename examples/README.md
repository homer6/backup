# Backup Examples

This directory contains example usage scenarios for the backup scripts. These examples provide guidance on how to effectively use the backup tools for various common scenarios.

## Available Examples

1. [S3 Backup Examples](s3_backup_examples.md) - Examples of backing up to/from S3 buckets
2. [GitHub Backup Examples](github_backup_examples.md) - Examples of backing up GitHub repositories
3. [Resumable Backup Examples](resumable_backup_examples.md) - Examples of using checkpointing for resumable backups
4. [Backup Automation](backup_automation.md) - Examples of automating backups with scripts and scheduling
5. [Common Scenarios](common_scenarios.md) - Real-world backup scenarios and solutions
6. [Nested Folder Examples](nested_folder_examples.md) - Examples specifically for backing up nested folder structures

## How to Use These Examples

The examples in this directory provide command-line examples that you can copy and adapt to your specific needs. Each example includes:

- A complete command line with all necessary parameters
- An explanation of what the command does
- Common variations and options

When using these examples, be sure to:

1. Replace bucket names, folder names, and paths with your own
2. Adjust AWS profiles as needed for your environment
3. Review parameter options to customize the backup behavior

## Common Parameters

Most backup commands support the following parameters:

- `--dest-profile`: AWS profile for destination bucket
- `--dest-bucket`: Destination S3 bucket name
- `--cleanup`: Remove temporary files after backup
- `--base-local-path`: Local path for temporary storage

## Further Reading

For more detailed information about the backup scripts, refer to:

- [S3 Backup Documentation](../docs/s3_backup.md)
- [GitHub Backup Documentation](../docs/github_backup.md)
- [Resumable Backups Documentation](../docs/resumable_backups.md)
- [Common Options](../docs/common.md)
- [Clearing Staging Area](../docs/clear_staging.md)

## Help and Support

If you encounter any issues or have questions about using these examples, please refer to the documentation or contact the development team.