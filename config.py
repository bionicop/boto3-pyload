import os
import logging
from pathlib import Path

# S3 Bucket Configuration
AWS_CONFIG = {
    'BUCKET_NAME': '24030142028',
    'BUCKET_REGION': 'ap-south-1',
    'DEFAULT_FILE_PATH': './assets/docs/something-to-look-at.txt',
    'DEFAULT_FILE_NAME': 'something-to-look-at.txt'
}

# Supported File Formats
SUPPORTED_FORMATS = {
    '.pdf': 'application/pdf',
    '.jpeg': 'image/jpeg', 
    '.mpeg': 'video/mpeg',
    '.doc': 'application/msword',
    '.txt': 'text/plain',
    '.zip': 'application/zip'
}

# Folder Organization
FOLDER_MAPPING = {
    'images': ['.jpeg'],
    'documents': ['.pdf', '.doc', '.txt'],
    'videos': ['.mpeg'],
    'archives': ['.zip'],
}

# Directory Settings
DIRECTORIES = {
    'DOWNLOADS': './downloads',
    'BACKUPS': './backups',
    'TEMP': './temp',
    'LOGS': './logs'
}

# Menu Configuration
MENU_OPERATIONS = {
    1: 'list', 2: 'create', 3: 'read', 4: 'update', 5: 'delete',
    6: 'organize', 7: 'backup', 8: 'sync', 9: 'zip', 10: 'exit'
}

MENU_ITEMS = [
    "List all buckets", "Upload file to bucket", "Read/Download file from bucket",
    "Update existing file", "Delete file from bucket", "Organize files into folders",
    "Create backup", "Start auto-sync", "Create and upload zip", "Exit"
]

# Messages
MESSAGES = {
    'SUCCESS': {
        'BUCKET_CREATED': "Bucket '{bucket_name}' created successfully",
        'FILE_UPLOADED': "'{file_key}' uploaded successfully to '{bucket_name}'",
        'FILE_UPDATED': "'{file_key}' updated successfully",
        'FILE_DELETED': "'{file_key}' deleted successfully",
        'FILE_DOWNLOADED': "'{file_key}' downloaded successfully to '{download_path}'",
        'OPERATION_COMPLETED': "Operation completed successfully",
        'BACKUP_CREATED': "Backup created successfully at {backup_path}",
        'BACKUP_RESTORED': "Backup restored successfully",
        'FILES_ORGANIZED': "Files organized successfully"
    },
    'ERROR': {
        'FILE_NOT_FOUND': "File not found: {file_path}",
        'UNSUPPORTED_FORMAT': "File format not supported: {file_path}",
        'BUCKET_ACCESS_ERROR': "Error accessing S3 bucket: {error}",
        'UPLOAD_FAILED': "Failed to upload file: {error}",
        'DOWNLOAD_FAILED': "Failed to download file: {error}",
        'INVALID_CHOICE': "Invalid choice. Please try again.",
        'OPERATION_CANCELLED': "Operation cancelled by user",
        'NO_FILES_FOUND': "No files found in bucket",
        'BACKUP_FAILED': "Failed to create backup",
        'RESTORE_FAILED': "Failed to restore backup"
    },
    'INFO': {
        'CURRENT_DIRECTORY': "Current directory: {directory}",
        'FILES_IN_BUCKET': "Files in bucket '{bucket_name}': {files}",
        'BUCKETS_FOUND': "Found {count} buckets in your account",
        'FILE_FORMAT_SUPPORTED': "File format is supported: {file_path}",
        'STARTING_OPERATION': "Starting {operation} operation...",
        'CHECKING_FILES': "Checking files in bucket '{bucket_name}'...",
        'CREATING_FOLDER': "Creating folder: {folder_path}"
    },
    'CONFIRM': {
        'DELETE_FILE': "Are you sure you want to delete '{file_key}' from bucket '{bucket_name}'? (y/N): ",
        'UPDATE_FILE': "Are you sure you want to update '{file_key}' in bucket '{bucket_name}'? (y/N): ",
        'OVERWRITE_FILE': "File '{file_name}' already exists locally. Overwrite? (y/N): ",
        'ORGANIZE_FILES': "This will move files into organized folders. Continue? (y/N): ",
        'CREATE_BACKUP': "This will create a backup of all files. Continue? (y/N): ",
        'RESTORE_BACKUP': "Are you sure you want to restore backup '{backup_name}'? This may overwrite existing files. (y/N): ",
        'START_SYNC': "Start auto-sync monitoring for configured directories? (y/N): ",
        'STOP_SYNC': "Stop auto-sync monitoring? (y/N): ",
        'TEST_SYNC': "Upload this file as a test? (y/N): "
    },
    'PROMPTS': {
        'ENTER_FILE_PATH': "Enter local file path: ",
        'ENTER_FILE_NUMBER': "Enter file number: ",
        'CHOOSE_OPERATION': "Choose operation (1-10): ",
        'ENTER_BUCKET_NAME': "Enter bucket name: ",
        'ENTER_DOWNLOAD_PATH': "Enter download path (or press Enter for default): "
    }
}

# Utility Functions
def ensure_directories():
    for dir_name, dir_path in DIRECTORIES.items():
        Path(dir_path).mkdir(parents=True, exist_ok=True)

def get_file_category(file_extension):
    file_extension = file_extension.lower()
    for category, extensions in FOLDER_MAPPING.items():
        if file_extension in extensions:
            return category
    return 'others'

def setup_logging(verbose=False):
    ensure_directories()
    log_level = logging.INFO if verbose else logging.ERROR
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('logs/aws_s3_operations.log')
        ]
    )

def get_confirmation(prompt_key, **kwargs):
    prompt = MESSAGES['CONFIRM'][prompt_key].format(**kwargs)
    response = input(prompt).strip().lower()
    return response in ['y', 'yes']

def print_message(category, message_key, **kwargs):
    message = MESSAGES[category][message_key].format(**kwargs)
    print(message)
    if category == 'ERROR':
        logging.error(message)
    else:
        logging.info(message)

def is_supported_format(file_path):
    file_extension = os.path.splitext(file_path)[1].lower()
    return file_extension in SUPPORTED_FORMATS

def validate_file_path(file_path):
    if not os.path.exists(file_path):
        print_message('ERROR', 'FILE_NOT_FOUND', file_path=file_path)
        print_message('INFO', 'CURRENT_DIRECTORY', directory=os.getcwd())
        return False
    
    if not is_supported_format(file_path):
        print_message('ERROR', 'UNSUPPORTED_FORMAT', file_path=file_path)
        return False
    
    print_message('INFO', 'FILE_FORMAT_SUPPORTED', file_path=file_path)
    return True