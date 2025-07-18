import os
import zipfile
import logging
from datetime import datetime
from pathlib import Path
from config import DIRECTORIES

class ArchiveManager:
    def __init__(self, s3_client):
        self.s3_client = s3_client
        self.temp_dir = Path(DIRECTORIES['TEMP'])
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        self.logger = logging.getLogger(__name__)
    
    def create_zip(self, files, archive_name):
        """Create zip archive from files"""
        try:
            if not archive_name.endswith('.zip'):
                archive_name += '.zip'
            
            archive_path = self.temp_dir / archive_name
            
            with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for file_path in files:
                    if os.path.exists(file_path):
                        zipf.write(file_path, os.path.basename(file_path))
                        self.logger.info(f"Added to zip: {file_path}")
            
            self.logger.info(f"Created zip: {archive_path}")
            return str(archive_path)
        except Exception as e:
            self.logger.error(f"Failed to create zip: {str(e)}")
            return None
    
    def enable_versioning(self, bucket_name):
        """Enable versioning on S3 bucket"""
        try:
            self.s3_client.put_bucket_versioning(
                Bucket=bucket_name,
                VersioningConfiguration={'Status': 'Enabled'}
            )
            self.logger.info(f"Enabled versioning on bucket: {bucket_name}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to enable versioning: {str(e)}")
            return False
    
    def upload_versioned_zip(self, archive_path, bucket_name, s3_key=None):
        """Upload zip to versioned S3 bucket"""
        try:
            if not s3_key:
                filename = os.path.basename(archive_path)
                s3_key = f"archives/{filename}"
            
            # Enable versioning if not already enabled
            self.enable_versioning(bucket_name)
            
            # Upload with metadata
            extra_args = {
                'Metadata': {
                    'archive-type': 'zip',
                    'created-by': 'aws-s3-file-manager',
                    'upload-time': datetime.now().isoformat()
                }
            }
            
            self.s3_client.upload_file(archive_path, bucket_name, s3_key, ExtraArgs=extra_args)
            self.logger.info(f"Uploaded versioned zip: s3://{bucket_name}/{s3_key}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to upload zip: {str(e)}")
            return False
    
    def list_versions(self, bucket_name, archive_key):
        """List all versions of an archive"""
        try:
            response = self.s3_client.list_object_versions(
                Bucket=bucket_name,
                Prefix=archive_key
            )
            
            versions = []
            for version in response.get('Versions', []):
                if version['Key'] == archive_key:
                    versions.append({
                        'version_id': version['VersionId'],
                        'last_modified': version['LastModified'],
                        'size': version['Size']
                    })
            
            self.logger.info(f"Found {len(versions)} versions of {archive_key}")
            return versions
        except Exception as e:
            self.logger.error(f"Failed to list versions: {str(e)}")
            return []