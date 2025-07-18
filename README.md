# Boto3PYload

A comprehensive command-line tool for managing files in Amazon S3 buckets with advanced automation capabilities including intelligent file organization, automated backup systems, change detection with auto-sync, and archive management with versioning.

## Features

### Core S3 Operations
- **Interactive Menu System**: User-friendly command-line interface for all operations
- **File Upload/Download**: Support for multiple file formats with validation
- **Bucket Management**: List, create, and manage S3 buckets
- **File Operations**: Read, update, delete files with confirmation prompts
- **Comprehensive Logging**: Detailed operation logs with configurable verbosity

### Advanced Features
- **🗂️ Intelligent File Organization**: Automatically categorize and organize files into folders by type
- **💾 Backup Management**: Create manual and scheduled backups with compression and metadata
- **📦 Archive Management**: Create zip archives with versioning support

## Quick Start

### Prerequisites
- Python 3.7 or higher
- AWS account with S3 access
- AWS credentials configured (see [AWS Configuration](#aws-configuration))

### Installation

1. Clone or download the project files
2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure AWS credentials (see [AWS Configuration](#aws-configuration))

4. Update configuration in `config.py` with your bucket details

### Basic Usage

#### Interactive Mode (Recommended)
```bash
python main.py
```

#### Direct Operations
```bash
# List all buckets
python main.py --operation list

# Upload a file
python main.py --operation upload

# Download/read a file
python main.py --operation read

# Organize files into folders
python main.py --operation organize

# Create backup
python main.py --operation backup

# Enable verbose logging
python main.py --verbose --operation list
```

## Supported File Types

The application automatically categorizes files into the following folders:

| Category | Extensions | Folder |
|----------|------------|--------|
| Images | `.jpeg` | `images/` |
| Documents | `.pdf`, `.doc`, `.txt` | `documents/` |
| Videos | `.mpeg` | `videos/` |
| Archives | `.zip` | `archives/` |

## Advanced Features Guide

### 1. File Organization

Automatically organize files in your S3 bucket into categorized folders:

**Features:**
- Batch organization of existing files
- Automatic categorization on upload
- Preserves original filenames
- User confirmation for batch operations
- Progress tracking and error handling

**Usage:**
```bash
python main.py --operation organize
```

**What it does:**
- Scans all root-level files in your bucket
- Moves files to appropriate folders based on extension
- Shows progress and completion summary
- Maintains file integrity with copy-then-delete operations

### 2. Backup Management

Create and manage backups of your S3 bucket contents:

**Features:**
- Manual backup creation with timestamps
- Scheduled backups (daily/weekly)
- Compressed zip archives with metadata
- Backup listing and restoration
- Automatic cleanup of old backups

**Usage:**
```bash
python main.py --operation backup
```

**Backup Menu Options:**
1. **Create Manual Backup**: Immediate backup of all bucket files
2. **List Existing Backups**: View all available backups with details
3. **Restore from Backup**: Restore files from a selected backup
4. **Schedule Automatic Backups**: Set up daily or weekly automated backups

**Backup Storage:**
- Location: `./backups/` directory
- Naming: `{bucket_name}_{timestamp}.zip`
- Metadata: File count, size, creation time, checksums

### 3. Auto-Sync (Coming Soon)

### 4. Archive Management

Create and manage zip archives with S3 versioning:

**Features:**
- Create zip archives from selected files
- Upload to versioned S3 buckets
- Maintain version history
- Metadata tracking with checksums
- Optimized compression settings

## Configuration

### AWS Configuration

You need to configure AWS credentials using one of these methods:

#### Option 1: AWS CLI (Recommended)
```bash
aws configure
```

#### Option 2: Environment Variables
```bash
export AWS_ACCESS_KEY_ID=your_access_key
export AWS_SECRET_ACCESS_KEY=your_secret_key
export AWS_DEFAULT_REGION=your_region
```

#### Option 3: IAM Roles (for EC2/Lambda)
Configure IAM roles with appropriate S3 permissions.

### Application Configuration

Edit `config.py` to customize settings:

```python
# S3 Bucket Configuration
AWS_CONFIG = {
    'BUCKET_NAME': 'your-bucket-name',
    'BUCKET_REGION': 'your-region',
    'DEFAULT_FILE_PATH': './assets/docs/something-to-look-at.txt',
    'DEFAULT_FILE_NAME': 'something-to-look-at.txt'
}

# Directory Settings
DIRECTORIES = {
    'DOWNLOADS': './downloads',
    'BACKUPS': './backups',
    'TEMP': './temp',
    'LOGS': './logs'
}
```

## Project Structure

```
├── main.py                 # Main application entry point
├── config.py              # Configuration constants and utilities
├── file_organizer.py      # File organization service
├── backup_manager.py      # Backup management service
├── archive_manager.py     # Archive management service
├── requirements.txt       # Python dependencies
├── .gitignore            # Git ignore rules
├── assets/               # Sample files and resources
│   ├── docs/            # Document samples
│   └── images/          # Image samples
├── downloads/           # Downloaded files from S3
├── backups/            # Local backup storage
├── temp/               # Temporary processing files
├── logs/               # Application logs
└── .aws/               # AWS credentials (gitignored)
```

## Command Reference

### Available Operations

| Operation | Command | Description |
|-----------|---------|-------------|
| `list` | `--operation list` | List all S3 buckets |
| `upload` | `--operation upload` | Upload file to bucket |
| `read` | `--operation read` | Read/download file from bucket |
| `update` | `--operation update` | Update existing file |
| `delete` | `--operation delete` | Delete file from bucket |
| `organize` | `--operation organize` | Organize files into folders |
| `backup` | `--operation backup` | Access backup management |

### Command-Line Options

| Option | Short | Description |
|--------|-------|-------------|
| `--verbose` | `-v` | Enable verbose logging |
| `--operation` | `-o` | Specify direct operation |

## Logging

The application provides comprehensive logging:

- **Console Output**: Real-time operation feedback
- **Log Files**: Detailed logs saved to `logs/aws_s3_operations.log`
- **Verbosity Control**: Use `--verbose` flag for detailed information
- **Error Tracking**: All errors logged with timestamps and context

## Dependencies

- **boto3**: AWS SDK for Python (S3 operations)
- **watchdog**: File system monitoring (for auto-sync)
- **schedule**: Task scheduling (for automated backups)