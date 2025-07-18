import boto3
import argparse
import os
from pathlib import Path
from config import (
    AWS_CONFIG, SUPPORTED_FORMATS, MENU_OPERATIONS, MENU_ITEMS, DIRECTORIES,
    setup_logging, print_message, get_confirmation, validate_file_path,
    ensure_directories, MESSAGES
)

# Bucket Operations
def list_all_buckets(s3):
    """List all S3 buckets"""
    print_message('INFO', 'STARTING_OPERATION', operation='list buckets')
    try:
        buckets = s3.list_buckets()['Buckets']
        print("Buckets: ", buckets)
        print_message('INFO', 'BUCKETS_FOUND', count=len(buckets))
        return buckets
    except Exception as e:
        print_message('ERROR', 'BUCKET_ACCESS_ERROR', error=str(e))
        return []

def create_new_bucket(s3, bucket_name, bucket_region=None):
    """Create a new S3 bucket"""
    if bucket_region is None:
        bucket_region = AWS_CONFIG['BUCKET_REGION']
    
    print_message('INFO', 'STARTING_OPERATION', operation='create bucket')
    try:
        s3.create_bucket(
            Bucket=bucket_name,
            CreateBucketConfiguration={'LocationConstraint': bucket_region}
        )
        print_message('SUCCESS', 'BUCKET_CREATED', bucket_name=bucket_name)
        return True
    except Exception as e:
        print_message('ERROR', 'BUCKET_ACCESS_ERROR', error=str(e))
        return False

# File Operations
def upload_update_file(s3, file_local, bucket_name, file_key):
    """Upload file to S3 bucket"""
    try:
        s3.upload_file(file_local, bucket_name, file_key)
        print_message('SUCCESS', 'FILE_UPLOADED', file_key=file_key, bucket_name=bucket_name)
        return True
    except Exception as e:
        print_message('ERROR', 'UPLOAD_FAILED', error=str(e))
        return False

def download_file_from_bucket(s3, bucket_name, file_key, download_path=None):
    """Download file from S3 bucket to local downloads folder"""
    # Ensure downloads directory exists
    ensure_directories()
    
    if download_path is None:
        download_path = os.path.join(DIRECTORIES['DOWNLOADS'], file_key)
    
    # Create subdirectories if needed
    os.makedirs(os.path.dirname(download_path), exist_ok=True)
    
    # Check if file already exists locally
    if os.path.exists(download_path):
        if not get_confirmation('OVERWRITE_FILE', file_name=os.path.basename(download_path)):
            print_message('INFO', 'OPERATION_CANCELLED')
            return False
    
    try:
        s3.download_file(bucket_name, file_key, download_path)
        print_message('SUCCESS', 'FILE_DOWNLOADED', file_key=file_key, download_path=download_path)
        return True
    except Exception as e:
        print_message('ERROR', 'DOWNLOAD_FAILED', error=str(e))
        return False

def read_and_download_file(s3, bucket_name):
    """Read file content and optionally download it"""
    selected_file = choose_file_from_bucket(s3, bucket_name)
    if not selected_file:
        return None
    
    try:
        # Read and display content (for text files)
        file_extension = os.path.splitext(selected_file)[1].lower()
        if file_extension in ['.txt', '.md', '.json', '.xml', '.csv']:
            content = s3.get_object(Bucket=bucket_name, Key=selected_file)['Body'].read().decode('utf-8')
            print(f"\n-//- Content of '{selected_file}' -//-\n{content}")
        else:
            print(f"\n-//- Binary file '{selected_file}' - Content not displayed -//-")
        
        # Ask if user wants to download
        download_choice = input("\nDo you want to download this file? (y/N): ").strip().lower()
        if download_choice in ['y', 'yes']:
            download_file_from_bucket(s3, bucket_name, selected_file)
        
        return selected_file
    except Exception as e:
        print_message('ERROR', 'DOWNLOAD_FAILED', error=str(e))
        return None

def check_files_in_bucket(s3, bucket_name):
    """Check and list files in bucket"""
    print_message('INFO', 'CHECKING_FILES', bucket_name=bucket_name)
    try:
        files = s3.list_objects_v2(Bucket=bucket_name).get('Contents', [])
        files = [obj['Key'] for obj in files]
        print_message('INFO', 'FILES_IN_BUCKET', bucket_name=bucket_name, files=files)
        return files
    except Exception as e:
        print_message('ERROR', 'BUCKET_ACCESS_ERROR', error=str(e))
        return []

def choose_file_from_bucket(s3, bucket_name):
    """Choose a file from bucket with user interaction"""
    try:
        files = s3.list_objects_v2(Bucket=bucket_name).get('Contents', [])
        files = [obj['Key'] for obj in files]
        
        if not files:
            print_message('ERROR', 'NO_FILES_FOUND')
            return None
        
        # Show files with numbers
        print("\nFiles in bucket:")
        for i, file in enumerate(files, 1):
            print(f"{i}. {file}")
        
        # Get user choice
        try:
            choice = int(input(MESSAGES['PROMPTS']['ENTER_FILE_NUMBER'])) - 1
            if 0 <= choice < len(files):
                selected_file = files[choice]
                print(f"Selected: {selected_file}")
                return selected_file
            else:
                print_message('ERROR', 'INVALID_CHOICE')
                return None
        except ValueError:
            print_message('ERROR', 'INVALID_CHOICE')
            return None
    except Exception as e:
        print_message('ERROR', 'BUCKET_ACCESS_ERROR', error=str(e))
        return None

def update_file_in_bucket(s3, bucket_name, file_key):
    """Update existing file in bucket with confirmation"""
    if not get_confirmation('UPDATE_FILE', file_key=file_key, bucket_name=bucket_name):
        print_message('INFO', 'OPERATION_CANCELLED')
        return False
    
    print(f"\nUpdating '{file_key}' in bucket '{bucket_name}'")
    new_file_path = input(MESSAGES['PROMPTS']['ENTER_FILE_PATH']).strip().strip('"').strip("'")
    new_file_path = os.path.normpath(new_file_path)
    
    if not validate_file_path(new_file_path):
        return False
    
    try:
        s3.upload_file(new_file_path, bucket_name, file_key)
        print_message('SUCCESS', 'FILE_UPDATED', file_key=file_key)
        return True
    except Exception as e:
        print_message('ERROR', 'UPLOAD_FAILED', error=str(e))
        return False

def delete_file_from_bucket(s3, bucket_name, file_key):
    """Delete file from bucket with confirmation"""
    if not get_confirmation('DELETE_FILE', file_key=file_key, bucket_name=bucket_name):
        print_message('INFO', 'OPERATION_CANCELLED')
        return False
    
    try:
        s3.delete_object(Bucket=bucket_name, Key=file_key)
        print_message('SUCCESS', 'FILE_DELETED', file_key=file_key)
        return True
    except Exception as e:
        print_message('ERROR', 'BUCKET_ACCESS_ERROR', error=str(e))
        return False

def organize_files_in_bucket(s3, bucket_name):
    """Organize files in bucket into folders by type with user confirmation and progress tracking"""
    from file_organizer import FileOrganizer
    
    print_message('INFO', 'STARTING_OPERATION', operation='organize files')
    
    # Check if bucket has files
    try:
        response = s3.list_objects_v2(Bucket=bucket_name)
        objects = response.get('Contents', [])
        
        if not objects:
            print_message('ERROR', 'NO_FILES_FOUND')
            return False
        
        # Count files that need organization (root level files only)
        files_to_organize = [obj['Key'] for obj in objects if '/' not in obj['Key']]
        
        if not files_to_organize:
            print("\nAll files are already organized in folders.")
            return True
        
        # Show files that will be organized
        print(f"\nFiles to be organized ({len(files_to_organize)}):")
        for i, file_key in enumerate(files_to_organize, 1):
            file_extension = os.path.splitext(file_key)[1]
            from config import get_file_category
            category = get_file_category(file_extension)
            print(f"  {i}. {file_key} -> {category}/")
        
        # Get user confirmation
        if not get_confirmation('ORGANIZE_FILES'):
            print_message('INFO', 'OPERATION_CANCELLED')
            return False
        
        # Initialize organizer and track progress
        organizer = FileOrganizer(s3)
        files_moved = 0
        files_failed = 0
        
        print(f"\nOrganizing {len(files_to_organize)} files...")
        
        for i, file_key in enumerate(files_to_organize, 1):
            try:
                print(f"Processing {i}/{len(files_to_organize)}: {file_key}", end=" ... ")
                
                if organizer.organize_file(bucket_name, file_key):
                    files_moved += 1
                    print("✓ Moved")
                else:
                    files_failed += 1
                    print("✗ Failed")
                    
            except Exception as e:
                files_failed += 1
                print(f"✗ Error: {str(e)}")
                print_message('ERROR', 'BUCKET_ACCESS_ERROR', error=str(e))
        
        # Report results
        print(f"\nOrganization completed:")
        print(f"  Files moved: {files_moved}")
        if files_failed > 0:
            print(f"  Files failed: {files_failed}")
        
        if files_moved > 0:
            print_message('SUCCESS', 'FILES_ORGANIZED')
            
            # Show updated bucket structure
            print("\nUpdated bucket structure:")
            check_files_in_bucket(s3, bucket_name)
        
        return files_moved > 0
        
    except Exception as e:
        print_message('ERROR', 'BUCKET_ACCESS_ERROR', error=str(e))
        return False

def backup_files_in_bucket(s3, bucket_name):
    """Create backup of bucket files with menu options for listing, creating, and restoring"""
    from backup_manager import BackupManager
    
    backup_manager = BackupManager(s3)
    
    while True:
        print("\n=== Backup Management ===")
        print("1. Create manual backup")
        print("2. List existing backups")
        print("3. Restore from backup")
        print("4. Schedule automatic backups")
        print("5. Return to main menu")
        
        try:
            choice = int(input("Choose backup operation (1-5): "))
            
            if choice == 1:
                # Create manual backup
                if get_confirmation('CREATE_BACKUP'):
                    print_message('INFO', 'STARTING_OPERATION', operation='create backup')
                    
                    backup_path = backup_manager.create_backup(bucket_name)
                    if backup_path:
                        # Get backup summary
                        backup_info = backup_manager.get_backup_info(backup_path)
                        print(f"\n✓ Backup created successfully!")
                        print(f"  Location: {backup_path}")
                        print(f"  Files backed up: {backup_info['file_count']}")
                        print(f"  Total size: {backup_info['total_size_mb']:.2f} MB")
                        print(f"  Created at: {backup_info['created_at']}")
                        print_message('SUCCESS', 'BACKUP_CREATED', backup_path=backup_path)
                    else:
                        print_message('ERROR', 'BACKUP_FAILED')
                else:
                    print_message('INFO', 'OPERATION_CANCELLED')
            
            elif choice == 2:
                # List existing backups
                backups = backup_manager.list_backups()
                if backups:
                    print(f"\n=== Existing Backups ({len(backups)}) ===")
                    for i, backup in enumerate(backups, 1):
                        print(f"{i}. {backup['filename']}")
                        print(f"   Created: {backup['created_at']}")
                        print(f"   Size: {backup['size_mb']:.2f} MB")
                        print(f"   Files: {backup['file_count']}")
                        print()
                else:
                    print("\nNo backups found.")
            
            elif choice == 3:
                # Restore from backup
                backups = backup_manager.list_backups()
                if not backups:
                    print("\nNo backups available for restoration.")
                    continue
                
                print("\n=== Available Backups ===")
                for i, backup in enumerate(backups, 1):
                    print(f"{i}. {backup['filename']} ({backup['created_at']})")
                
                try:
                    backup_choice = int(input("Choose backup to restore (number): ")) - 1
                    if 0 <= backup_choice < len(backups):
                        selected_backup = backups[backup_choice]
                        
                        print(f"\nSelected backup: {selected_backup['filename']}")
                        print(f"This will restore {selected_backup['file_count']} files to bucket '{bucket_name}'")
                        
                        if get_confirmation('RESTORE_BACKUP', backup_name=selected_backup['filename']):
                            print_message('INFO', 'STARTING_OPERATION', operation='restore backup')
                            
                            if backup_manager.restore_backup(selected_backup['path'], bucket_name):
                                print(f"\n✓ Backup restored successfully!")
                                print(f"  Files restored: {selected_backup['file_count']}")
                                print_message('SUCCESS', 'BACKUP_RESTORED')
                            else:
                                print_message('ERROR', 'RESTORE_FAILED')
                        else:
                            print_message('INFO', 'OPERATION_CANCELLED')
                    else:
                        print_message('ERROR', 'INVALID_CHOICE')
                except ValueError:
                    print_message('ERROR', 'INVALID_CHOICE')
            
            elif choice == 4:
                # Schedule automatic backups
                print("\n=== Schedule Automatic Backups ===")
                print("1. Daily (2:00 AM)")
                print("2. Weekly (Sunday 2:00 AM)")
                print("3. Disable scheduled backups")
                
                try:
                    schedule_choice = int(input("Choose schedule option (1-3): "))
                    
                    if schedule_choice == 1:
                        if backup_manager.schedule_backup(bucket_name, 'daily'):
                            print("✓ Daily backups scheduled successfully")
                        else:
                            print("✗ Failed to schedule daily backups")
                    
                    elif schedule_choice == 2:
                        if backup_manager.schedule_backup(bucket_name, 'weekly'):
                            print("✓ Weekly backups scheduled successfully")
                        else:
                            print("✗ Failed to schedule weekly backups")
                    
                    elif schedule_choice == 3:
                        backup_manager.stop_scheduler()
                        print("✓ Scheduled backups disabled")
                    
                    else:
                        print_message('ERROR', 'INVALID_CHOICE')
                        
                except ValueError:
                    print_message('ERROR', 'INVALID_CHOICE')
            
            elif choice == 5:
                # Return to main menu
                break
            
            else:
                print_message('ERROR', 'INVALID_CHOICE')
                
        except ValueError:
            print_message('ERROR', 'INVALID_CHOICE')
        except KeyboardInterrupt:
            print("\n\nOperation cancelled by user.")
            break
        except Exception as e:
            print_message('ERROR', 'BUCKET_ACCESS_ERROR', error=str(e))

def auto_sync_files_in_bucket(s3, bucket_name):
    """Auto-sync functionality - Coming soon"""
    print("\n=== Auto-Sync ===")
    print("🚧 Under development")
    input("Press Enter to return to main menu...")

# def zip_files_in_bucket(s3, bucket_name):

# Menu Operations
def show_interactive_menu():
    """Display interactive menu and get user choice"""
    print("\n\n=== AWS S3 Operations Menu ===")
    for i, item in enumerate(MENU_ITEMS, 1):
        print(f"{i}. {item}")
    
    try:
        choice = int(input(MESSAGES['PROMPTS']['CHOOSE_OPERATION']))
        return MENU_OPERATIONS.get(choice, None)
    except ValueError:
        print_message('ERROR', 'INVALID_CHOICE')
        return None

# Main Execution
def main():
    """Main execution function"""
    # Setup command line arguments
    parser = argparse.ArgumentParser(description='AWS S3 Operations - Interactive menu or direct operations')
    parser.add_argument('--verbose', '-v', action='store_true', 
                        help='Enable verbose logging to see detailed information')
    parser.add_argument('--operation', '-o', 
                        choices=['list', 'create', 'upload', 'read', 'update', 'delete', 'organize', 'backup'], 
                        help='Direct operation (optional): list, create, upload, read, update, delete, organize, backup')
    args = parser.parse_args()
    
    # Setup logging and directories
    setup_logging(args.verbose)
    ensure_directories()
    
    # Initialize S3 Client
    print_message('INFO', 'STARTING_OPERATION', operation='S3 client initialization')
    s3 = boto3.client('s3')
    
    try:
        # Determine operation
        if not args.operation:
            operation = show_interactive_menu()
            if operation == 'exit' or operation is None:
                return
        else:
            operation = args.operation
        
        # Execute operations
        bucket_name = AWS_CONFIG['BUCKET_NAME']
        
        if operation == 'list':
            list_all_buckets(s3)
            
        elif operation == 'create' or operation == 'upload':
            file_path = input(MESSAGES['PROMPTS']['ENTER_FILE_PATH']).strip().strip('"').strip("'")
            file_path = os.path.normpath(file_path)
            
            if validate_file_path(file_path):
                file_name = os.path.basename(file_path)
                upload_update_file(s3, file_path, bucket_name, file_name)
                
        elif operation == 'read':
            read_and_download_file(s3, bucket_name)
                
        elif operation == 'update':
            selected_file = choose_file_from_bucket(s3, bucket_name)
            if selected_file:
                update_file_in_bucket(s3, bucket_name, selected_file)
                
        elif operation == 'delete':
            selected_file = choose_file_from_bucket(s3, bucket_name)
            if selected_file:
                delete_file_from_bucket(s3, bucket_name, selected_file)
                
        elif operation == 'organize':
            organize_files_in_bucket(s3, bucket_name)
            
        elif operation == 'backup':
            backup_files_in_bucket(s3, bucket_name)
            
        elif operation == 'sync':
            auto_sync_files_in_bucket(s3, bucket_name)
        
        # Show current files at the end (except for list operation)
        if operation != 'list':
            print("\n" + "="*50)
            print("Current files in bucket:")
            check_files_in_bucket(s3, bucket_name)
        
        print_message('SUCCESS', 'OPERATION_COMPLETED')
        
    except Exception as e:
        print_message('ERROR', 'BUCKET_ACCESS_ERROR', error=str(e))

if __name__ == "__main__":
    main()