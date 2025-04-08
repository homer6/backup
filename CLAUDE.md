# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands
- Run S3 backup: `python backup_s3.py [folder_name]`
- Run GitHub backup: `python backup_github.py <org_name>`
- Run Pack: `python pack.py <folder_path>`
- Run Unpack: `python unpack.py <destination_folder> --s3-path <s3-path>`
- Lint: `flake8 *.py`
- Format: `black *.py`
- Type check: `mypy *.py`

## Code Style Guidelines
- **Imports**: Group standard library, third-party, and local imports separated by empty line
- **Formatting**: Use Black default settings (max line length 88)
- **Types**: Not currently used, but if added, use type hints compatible with mypy
- **Naming**: Use snake_case for variables/functions, UPPER_CASE for constants
- **Error Handling**: Use specific exception types and provide clear error messages
- **Function Organization**: Keep functions small, with clear docstrings
- **Comments**: Add TODO comments for future improvements
- **Constants**: Define constants at top of file
- **Subprocess**: Always use subprocess.run() with proper error handling

## Important Reminders
- Always consider updating the documentation (README.md and usage examples) when modifying functionality