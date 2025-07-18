import os
import zipfile
import schedule
import threading
import time
import logging
from datetime import datetime
from pathlib import Path
from config import DIRECTORIES

class BackupManager:
    def __init__(self, s3_client):
        self.s3_client = s3_client
        self.backup_dir = Path(DIRECTORIES['BACKUPS'])
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.logger = logging.getLogger(__name__)
        self.scheduler_running = False
    
    def create_backup(self, bucket_name):
        """Create zip backup of all bucket files"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"{bucket_name}_{timestamp}.zip"
            backup_path = self.backup_dir / backup_filename
            
            # Get all files from bucket
            response = self.s3_client.list_objects_v2(Bucket=bucket_name)
            objects = response.get('Contents', [])
            
            if not objects:
                self.logger.warning("No files found in bucket")
                return False
            
            # Create zip backup
            with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for obj in objects:
                    file_key = obj['Key']
                    temp_file = Path(DIRECTORIES['TEMP']) / file_key.replace('/', '_')
                    temp_file.parent.mkdir(parents=True, exist_ok=True)
                    
                    # Download file and add to zip
                    self.s3_client.download_file(bucket_name, file_key, str(temp_file))
                    zipf.write(temp_file, file_key)
                    temp_file.unlink()  # Clean up temp file
            
            self.logger.info(f"Backup created: {backup_path}")
            return str(backup_path)
        except Exception as e:
            self.logger.error(f"Backup failed: {str(e)}")
            return False
    
    def schedule_backup(self, bucket_name, interval='daily'):
        """Schedule automatic backups"""
        try:
            schedule.clear()  # Clear existing schedules
            
            if interval == 'daily':
                schedule.every().day.at("02:00").do(self.create_backup, bucket_name)
            elif interval == 'weekly':
                schedule.every().sunday.at("02:00").do(self.create_backup, bucket_name)
            
            # Start scheduler thread
            if not self.scheduler_running:
                self.scheduler_running = True
                scheduler_thread = threading.Thread(target=self._run_scheduler, daemon=True)
                scheduler_thread.start()
            
            self.logger.info(f"Scheduled {interval} backup for {bucket_name}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to schedule backup: {str(e)}")
            return False
    
    def _run_scheduler(self):
        """Run scheduler in background thread"""
        while self.scheduler_running:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    
    def get_backup_info(self, backup_path):
        """Get detailed information about a backup file"""
        try:
            backup_file = Path(backup_path)
            if not backup_file.exists():
                return None
            
            # Get file stats
            stat = backup_file.stat()
            size_mb = stat.st_size / (1024 * 1024)
            created_at = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
            
            # Count files in zip
            file_count = 0
            try:
                with zipfile.ZipFile(backup_path, 'r') as zipf:
                    file_count = len(zipf.namelist())
            except:
                file_count = 0
            
            return {
                'filename': backup_file.name,
                'path': str(backup_path),
                'file_count': file_count,
                'total_size_mb': size_mb,
                'created_at': created_at
            }
        except Exception as e:
            self.logger.error(f"Failed to get backup info: {str(e)}")
            return None
    
    def list_backups(self):
        """List all available backup files"""
        try:
            backups = []
            backup_files = list(self.backup_dir.glob("*.zip"))
            
            for backup_file in sorted(backup_files, key=lambda x: x.stat().st_mtime, reverse=True):
                backup_info = self.get_backup_info(str(backup_file))
                if backup_info:
                    backups.append(backup_info)
            
            return backups
        except Exception as e:
            self.logger.error(f"Failed to list backups: {str(e)}")
            return []
    
    def restore_backup(self, backup_path, bucket_name):
        """Restore files from backup to S3 bucket"""
        try:
            backup_file = Path(backup_path)
            if not backup_file.exists():
                self.logger.error(f"Backup file not found: {backup_path}")
                return False
            
            # Extract and upload files from backup
            with zipfile.ZipFile(backup_path, 'r') as zipf:
                temp_extract_dir = Path(DIRECTORIES['TEMP']) / 'restore_temp'
                temp_extract_dir.mkdir(parents=True, exist_ok=True)
                
                try:
                    # Extract all files
                    zipf.extractall(temp_extract_dir)
                    
                    # Upload each file to S3
                    for file_path in temp_extract_dir.rglob('*'):
                        if file_path.is_file():
                            # Calculate relative path for S3 key
                            relative_path = file_path.relative_to(temp_extract_dir)
                            s3_key = str(relative_path).replace('\\', '/')
                            
                            # Upload to S3
                            self.s3_client.upload_file(str(file_path), bucket_name, s3_key)
                            self.logger.info(f"Restored file: {s3_key}")
                    
                    # Clean up temp directory
                    import shutil
                    shutil.rmtree(temp_extract_dir)
                    
                    self.logger.info(f"Backup restored successfully from {backup_path}")
                    return True
                    
                except Exception as e:
                    # Clean up temp directory on error
                    import shutil
                    if temp_extract_dir.exists():
                        shutil.rmtree(temp_extract_dir)
                    raise e
                    
        except Exception as e:
            self.logger.error(f"Failed to restore backup: {str(e)}")
            return False
    
    def stop_scheduler(self):
        """Stop the backup scheduler"""
        try:
            self.scheduler_running = False
            schedule.clear()
            self.logger.info("Backup scheduler stopped")
            return True
        except Exception as e:
            self.logger.error(f"Failed to stop scheduler: {str(e)}")
            return False