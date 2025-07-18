# Troubleshooting Guide

This guide helps you resolve common issues with the AWS S3 File Manager and its advanced features.

## Table of Contents

- [Quick Diagnostics](#quick-diagnostics)
- [AWS Configuration Issues](#aws-configuration-issues)
- [File Operation Issues](#file-operation-issues)
- [File Organization Issues](#file-organization-issues)
- [Backup Issues](#backup-issues)
- [Auto-Sync Issues](#auto-sync-issues)
- [Archive Management Issues](#archive-management-issues)
- [Performance Issues](#performance-issues)
- [Logging and Debugging](#logging-and-debugging)
- [Common Error Messages](#common-error-messages)

## Quick Diagnostics

### Check System Status

Run these commands to quickly diagnose common issues:

```bash
# Check if Python dependencies are installed
python -c "import boto3, watchdog, schedule; print('All dependencies installed')"

# Check AWS credentials
python -c "import boto3; print('Credentials OK' if boto3.Session().get_credentials() else 'No credentials')"

# Check if directories exist
python -c "import os; dirs=['downloads','backups','temp','logs']; [print(f'{d}: {os.path.exists(d)}') for d in dirs]"

# Test basic S3 connection
python -c "import boto3; s3=boto3.client('s3'); print(f'Buckets: {len(s3.list_buckets()[\"Buckets\"])}')"
```

### Enable Verbose Logging

For detailed troubleshooting information:

```bash
python main.py --verbose
```

## AWS Configuration Issues

### Issue: "NoCredentialsError: Unable to locate credentials"

**Symptoms:**
- Application fails to start
- Error message about missing credentials
- Cannot list buckets

**Solutions:**

1. **Configure AWS CLI:**
```bash
aws configure
```

2. **Set Environment Variables:**
```bash
# Linux/macOS
export AWS_ACCESS_KEY_ID=your_access_key
export AWS_SECRET_ACCESS_KEY=your_secret_key
export AWS_DEFAULT_REGION=your_region

# Windows
set AWS_ACCESS_KEY_ID=your_access_key
set AWS_SECRET_ACCESS_KEY=your_secret_key
set AWS_DEFAULT_REGION=your_region
```

3. **Check Credentials File:**
Ensure `~/.aws/credentials` exists and contains:
```ini
[default]
aws_access_key_id = YOUR_ACCESS_KEY
aws_secret_access_key = YOUR_SECRET_KEY
```

4. **Verify Permissions:**
Your AWS user needs these S3 permissions:
- `s3:ListBucket`
- `s3:GetObject`
- `s3:PutObject`
- `s3:DeleteObject`
- `s3:PutBucketVersioning`
- `s3:GetBucketVersioning`

### Issue: "AccessDenied" or "Forbidden" Errors

**Symptoms:**
- Can list buckets but cannot access files
- Upload/download operations fail
- Backup operations fail

**Solutions:**

1. **Check IAM Permissions:**
Ensure your user has the required S3 permissions for your bucket.

2. **Verify Bucket Policy:**
Check if bucket policy allows your user access.

3. **Check Bucket Region:**
Ensure `BUCKET_REGION` in `config.py` matches your bucket's actual region.

### Issue: "BucketNotFound" Error

**Symptoms:**
- Error when trying to access bucket
- Bucket name appears correct

**Solutions:**

1. **Verify Bucket Name:**
Check `BUCKET_NAME` in `config.py` is exactly correct (case-sensitive).

2. **Check Region:**
Ensure you're connecting to the correct region.

3. **List All Buckets:**
```bash
python main.py --operation list
```

## File Operation Issues

### Issue: Files Not Uploading

**Symptoms:**
- Upload appears to succeed but file not in S3
- Upload fails with timeout
- Large files fail to upload

**Solutions:**

1. **Check File Path:**
```bash
# Verify file exists
ls -la "path/to/your/file"
```

2. **Check File Size:**
Very large files may timeout. Consider:
- Splitting large files
- Increasing timeout settings
- Using multipart upload for files >100MB

3. **Check File Permissions:**
Ensure the application can read the file:
```bash
# Linux/macOS
chmod 644 your_file

# Windows - check file properties
```

4. **Network Issues:**
Test with a small file first to isolate network problems.

### Issue: Downloads Failing

**Symptoms:**
- Download starts but fails partway
- Downloaded files are corrupted
- Permission errors during download

**Solutions:**

1. **Check Disk Space:**
```bash
# Linux/macOS
df -h

# Windows
dir
```

2. **Check Download Directory Permissions:**
```bash
# Linux/macOS
chmod 755 downloads/

# Windows - check folder properties
```

3. **Verify File Integrity:**
Compare file sizes between S3 and local copy.

## File Organization Issues

### Issue: Files Not Being Organized

**Symptoms:**
- Organization operation completes but files remain in root
- Some files organized, others not
- Error messages during organization

**Solutions:**

1. **Check File Extensions:**
Ensure file extensions are supported in `FOLDER_MAPPING`:
```python
# In config.py
FOLDER_MAPPING = {
    'images': ['.jpeg', '.jpg', '.png'],  # Add missing extensions
    'documents': ['.pdf', '.doc', '.txt'],
    # ... other mappings
}
```

2. **Check for Existing Folders:**
Files already in folders are skipped. To reorganize all files:
- Manually move files to root level first
- Or modify the organization logic

3. **Permission Issues:**
Ensure the application has permission to copy/delete objects in S3.

4. **Large Number of Files:**
For buckets with many files, the operation may take time. Check logs for progress.

### Issue: Files Going to Wrong Folders

**Symptoms:**
- Files categorized incorrectly
- All files going to "others" folder

**Solutions:**

1. **Check File Extensions:**
```python
# Debug file extension detection
import os
file_path = "your_file.ext"
extension = os.path.splitext(file_path)[1].lower()
print(f"Extension: {extension}")
```

2. **Update FOLDER_MAPPING:**
Add missing file types to the appropriate categories.

3. **Case Sensitivity:**
Extensions are converted to lowercase, ensure mapping uses lowercase.

## Backup Issues

### Issue: Backup Creation Fails

**Symptoms:**
- Backup operation starts but fails
- Partial backup files created
- Out of disk space errors

**Solutions:**

1. **Check Disk Space:**
Ensure sufficient space in backup directory:
```bash
# Check available space
df -h ./backups/
```

2. **Check Backup Directory Permissions:**
```bash
# Linux/macOS
chmod 755 backups/
mkdir -p backups/
```

3. **Large Bucket Issues:**
For very large buckets:
- Increase timeout settings
- Consider selective backup
- Monitor memory usage

4. **Network Timeouts:**
For buckets with many files, downloads may timeout:
- Run backup during off-peak hours
- Consider implementing resume functionality

### Issue: Backup Restoration Fails

**Symptoms:**
- Restoration starts but fails partway
- Some files restored, others missing
- Permission errors during restoration

**Solutions:**

1. **Check Backup File Integrity:**
```bash
# Test zip file
unzip -t backups/your_backup.zip
```

2. **Check S3 Permissions:**
Ensure write permissions to target bucket.

3. **Check Available Space:**
Ensure sufficient space for temporary extraction.

### Issue: Scheduled Backups Not Running

**Symptoms:**
- Scheduled backups configured but not executing
- No backup files created at scheduled times
- No error messages

**Solutions:**

1. **Check Scheduler Status:**
The scheduler runs in a background thread. Ensure the main application stays running.

2. **Check System Time:**
Ensure system time is correct for scheduled execution.

3. **Check Logs:**
Look for scheduler-related messages in logs.

4. **Manual Test:**
Test backup creation manually first to ensure it works.

## Auto-Sync Issues

### Issue: File Changes Not Detected

**Symptoms:**
- Files modified but not synced
- Sync appears to be running but no activity
- New files not uploaded

**Solutions:**

1. **Check Watch Directories:**
Ensure directories in sync configuration exist and are accessible.

2. **File System Permissions:**
Ensure the application can read the watched directories.

3. **File System Type:**
Some network drives or special file systems may not support file watching.

4. **Check Exclusion Patterns:**
Verify files aren't being excluded by sync patterns.

### Issue: Sync Conflicts

**Symptoms:**
- Files exist both locally and remotely with different content
- Sync stops with conflict errors
- Unexpected file versions

**Solutions:**

1. **Configure Conflict Resolution:**
Set appropriate conflict resolution strategy in configuration.

2. **Manual Resolution:**
Resolve conflicts manually by choosing which version to keep.

3. **Backup Before Sync:**
Always backup important files before enabling auto-sync.

## Archive Management Issues

### Issue: Archive Creation Fails

**Symptoms:**
- Archive creation starts but fails
- Corrupted archive files
- Out of memory errors

**Solutions:**

1. **Check Available Memory:**
Large archives require significant memory. Consider:
- Creating smaller archives
- Increasing system memory
- Processing files in batches

2. **Check File Permissions:**
Ensure all files to be archived are readable.

3. **Check Disk Space:**
Ensure sufficient space for temporary archive creation.

### Issue: Versioning Not Working

**Symptoms:**
- Archives uploaded but no version history
- Cannot retrieve previous versions
- Versioning appears disabled

**Solutions:**

1. **Check Bucket Versioning:**
```bash
# Check if versioning is enabled
aws s3api get-bucket-versioning --bucket your-bucket-name
```

2. **Enable Versioning:**
The application should enable versioning automatically, but you can do it manually:
```bash
aws s3api put-bucket-versioning --bucket your-bucket-name --versioning-configuration Status=Enabled
```

3. **Check Permissions:**
Ensure your user has `s3:PutBucketVersioning` permission.

## Performance Issues

### Issue: Slow Operations

**Symptoms:**
- File uploads/downloads take very long
- Backup creation is extremely slow
- Application becomes unresponsive

**Solutions:**

1. **Check Network Connection:**
Test internet speed and stability.

2. **Optimize File Sizes:**
- Compress files before upload
- Use appropriate compression levels
- Consider file size limits

3. **Parallel Processing:**
For multiple files, consider processing in parallel (advanced users).

4. **Regional Optimization:**
Ensure your bucket region is geographically close to your location.

### Issue: High Memory Usage

**Symptoms:**
- System becomes slow during operations
- Out of memory errors
- Application crashes

**Solutions:**

1. **Process Files in Batches:**
Instead of processing all files at once, process in smaller batches.

2. **Increase System Memory:**
Consider upgrading system RAM for large operations.

3. **Monitor Memory Usage:**
```bash
# Linux/macOS
top -p $(pgrep -f python)

# Windows
tasklist | findstr python
```

## Logging and Debugging

### Enable Debug Logging

Add debug logging to troubleshoot issues:

```python
# In config.py, modify setup_logging function
def setup_logging(verbose=False):
    log_level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('logs/aws_s3_operations.log')
        ]
    )
```

### Check Log Files

```bash
# View recent log entries
tail -f logs/aws_s3_operations.log

# Search for specific errors
grep -i error logs/aws_s3_operations.log

# View all logs
cat logs/aws_s3_operations.log
```

### Debug Network Issues

```bash
# Test S3 connectivity
aws s3 ls s3://your-bucket-name

# Test with curl
curl -I https://s3.amazonaws.com

# Check DNS resolution
nslookup s3.amazonaws.com
```

## Common Error Messages

### "ModuleNotFoundError: No module named 'boto3'"

**Solution:**
```bash
pip install -r requirements.txt
```

### "FileNotFoundError: [Errno 2] No such file or directory"

**Solutions:**
1. Check file path is correct
2. Use absolute paths instead of relative paths
3. Ensure file exists before operation

### "PermissionError: [Errno 13] Permission denied"

**Solutions:**
1. Check file/directory permissions
2. Run with appropriate user privileges
3. Ensure directories are writable

### "ConnectionError: Failed to establish a new connection"

**Solutions:**
1. Check internet connection
2. Verify AWS service status
3. Check firewall settings
4. Try different AWS region

### "ClientError: An error occurred (NoSuchBucket)"

**Solutions:**
1. Verify bucket name in config.py
2. Check bucket exists in correct region
3. Ensure proper AWS credentials

### "UnicodeDecodeError" or "UnicodeEncodeError"

**Solutions:**
1. Ensure file names use valid characters
2. Check file encoding for text files
3. Use UTF-8 encoding when possible

## Getting Help

### Before Seeking Help

1. **Check Logs:**
   - Review `logs/aws_s3_operations.log`
   - Run with `--verbose` flag

2. **Test Basic Functionality:**
   - Try listing buckets
   - Test with small files first
   - Verify AWS credentials

3. **Check Configuration:**
   - Verify all settings in `config.py`
   - Ensure directories exist
   - Check file permissions

### Information to Provide

When reporting issues, include:

1. **Error Message:** Complete error message and stack trace
2. **Operation:** What you were trying to do
3. **Environment:** OS, Python version, dependency versions
4. **Configuration:** Relevant parts of your configuration (without credentials)
5. **Log Files:** Relevant log entries
6. **Steps to Reproduce:** Exact steps that cause the issue

### Diagnostic Commands

Run these commands and include output when reporting issues:

```bash
# System information
python --version
pip list | grep -E "(boto3|watchdog|schedule)"

# AWS configuration test
aws configure list

# Directory structure
ls -la

# Log file tail
tail -20 logs/aws_s3_operations.log
```

## Prevention Tips

1. **Regular Backups:** Always backup important data before major operations
2. **Test First:** Test operations with small files/datasets first
3. **Monitor Logs:** Regularly check log files for warnings
4. **Keep Updated:** Keep dependencies updated
5. **Validate Config:** Regularly validate configuration settings
6. **Monitor Usage:** Keep track of AWS usage and costs

## Advanced Troubleshooting

### Network Debugging

```bash
# Test AWS connectivity
telnet s3.amazonaws.com 443

# Check routing
traceroute s3.amazonaws.com

# Test with different regions
aws s3 ls --region us-east-1
aws s3 ls --region eu-west-1
```

### Python Environment Issues

```bash
# Check Python path
python -c "import sys; print(sys.path)"

# Check installed packages
pip freeze

# Create clean environment
python -m venv clean_env
source clean_env/bin/activate  # Linux/macOS
# or
clean_env\Scripts\activate     # Windows
pip install -r requirements.txt
```

### AWS CLI Debugging

```bash
# Enable AWS CLI debug mode
aws s3 ls --debug

# Check AWS CLI configuration
aws configure list-profiles
aws sts get-caller-identity
```

This troubleshooting guide should help you resolve most common issues. If problems persist, ensure you have the latest version of all dependencies and consider creating a minimal test case to isolate the issue.