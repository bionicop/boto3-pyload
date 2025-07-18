import os
import logging
from config import FOLDER_MAPPING

class FileOrganizer:
    def __init__(self, s3_client):
        self.s3_client = s3_client
        self.logger = logging.getLogger(__name__)
    
    def get_file_category(self, file_extension):
        """Get folder category for file extension"""
        file_extension = file_extension.lower()
        for category, extensions in FOLDER_MAPPING.items():
            if file_extension in extensions:
                return category
        return 'others'
    
    def organize_file(self, bucket_name, file_key):
        """Move single file to appropriate folder"""
        try:
            file_extension = os.path.splitext(file_key)[1]
            category = self.get_file_category(file_extension)
            
            # Skip if already in folder
            if file_key.startswith(f"{category}/"):
                return True
            
            # Create new key with folder
            new_key = f"{category}/{os.path.basename(file_key)}"
            
            # Copy to new location and delete original
            copy_source = {'Bucket': bucket_name, 'Key': file_key}
            self.s3_client.copy_object(CopySource=copy_source, Bucket=bucket_name, Key=new_key)
            self.s3_client.delete_object(Bucket=bucket_name, Key=file_key)
            
            self.logger.info(f"Organized {file_key} -> {new_key}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to organize {file_key}: {str(e)}")
            return False
    
    def organize_bucket(self, bucket_name):
        """Organize all files in bucket into folders"""
        try:
            response = self.s3_client.list_objects_v2(Bucket=bucket_name)
            objects = response.get('Contents', [])
            
            files_moved = 0
            for obj in objects:
                file_key = obj['Key']
                # Only organize root files (not already in folders)
                if '/' not in file_key:
                    if self.organize_file(bucket_name, file_key):
                        files_moved += 1
            
            self.logger.info(f"Organized {files_moved} files")
            return files_moved
        except Exception as e:
            self.logger.error(f"Failed to organize bucket: {str(e)}")
            return 0