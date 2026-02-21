"""
File Uploader Utility for Social Media Integration

This module provides utilities to upload files to temporary public storage
for use with APIs that require publicly accessible URLs (like Instagram).
"""

import os
import logging
import asyncio
import subprocess
from pathlib import Path
from typing import Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class FileUploader:
    """
    Utility class for uploading files to temporary public storage.
    
    Uses manus-upload-file command to upload files to S3 and get public URLs.
    """
    
    @staticmethod
    async def upload_to_public_url(file_path: str) -> Optional[str]:
        """
        Upload a file to temporary public storage and return the public URL.
        
        Args:
            file_path: Path to the file to upload
            
        Returns:
            Public URL of the uploaded file, or None if upload fails
        """
        if not os.path.exists(file_path):
            logger.error(f"File not found: {file_path}")
            return None
        
        try:
            # Use manus-upload-file to upload the file
            result = await FileUploader._run_command(
                ["manus-upload-file", file_path]
            )
            
            if result and result.strip():
                public_url = result.strip()
                logger.info(f"File uploaded successfully: {public_url}")
                return public_url
            else:
                logger.error("Upload command returned empty result")
                return None
        
        except Exception as e:
            logger.error(f"Error uploading file: {e}")
            return None
    
    @staticmethod
    async def _run_command(cmd: list) -> Optional[str]:
        """
        Run a shell command asynchronously and return the output.
        
        Args:
            cmd: Command and arguments as a list
            
        Returns:
            Command output as string, or None if command fails
        """
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                return stdout.decode('utf-8')
            else:
                error_msg = stderr.decode('utf-8')
                logger.error(f"Command failed: {error_msg}")
                return None
        
        except Exception as e:
            logger.error(f"Error running command: {e}")
            return None


# Convenience function
async def get_public_url(file_path: str) -> Optional[str]:
    """
    Get a public URL for a local file by uploading it to temporary storage.
    
    Args:
        file_path: Path to the file
        
    Returns:
        Public URL of the uploaded file
    """
    return await FileUploader.upload_to_public_url(file_path)


__all__ = [
    "FileUploader",
    "get_public_url"
]
