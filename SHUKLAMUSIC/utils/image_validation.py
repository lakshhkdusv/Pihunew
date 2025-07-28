"""
Image validation utilities for SHUKLAMUSIC bot.
Provides functions to safely download and validate images from Telegram.
"""

import os
from typing import Optional
from PIL import Image, UnidentifiedImageError
from SHUKLAMUSIC import app


async def safe_download_media(file_id: str, max_retries: int = 3) -> Optional[str]:
    """
    Safely download media from Telegram with validation and retry logic.
    
    Args:
        file_id: The file ID to download
        max_retries: Maximum number of retry attempts
        
    Returns:
        Path to downloaded file if successful, None otherwise
    """
    for attempt in range(max_retries):
        try:
            photo_path = await app.download_media(file_id)
            
            # Ensure photo is a string path, not a file object
            if not isinstance(photo_path, str):
                print(f"Downloaded media is not a file path: {type(photo_path)}")
                continue
                
            if not photo_path or not os.path.exists(photo_path):
                print(f"Downloaded photo does not exist: {photo_path}")
                continue
                
            # Validate the downloaded file
            if validate_image_file(photo_path):
                return photo_path
            else:
                # Clean up invalid file
                try:
                    if os.path.exists(photo_path):
                        os.remove(photo_path)
                except OSError:
                    pass
                    
        except Exception as e:
            print(f"Error downloading media (attempt {attempt + 1}/{max_retries}): {e}")
            
    return None


def validate_image_file(file_path: str) -> bool:
    """
    Validate that a file is a proper image file.
    
    Args:
        file_path: Path to the image file
        
    Returns:
        True if valid image, False otherwise
    """
    try:
        # Check if file exists
        if not os.path.exists(file_path):
            print(f"Image file does not exist: {file_path}")
            return False
            
        # Check file size (less than 100 bytes is likely corrupted)
        file_size = os.path.getsize(file_path)
        if file_size < 100:
            print(f"Image file is too small (corrupted): {file_path} - {file_size} bytes")
            return False
            
        # Try to open and verify the image
        with Image.open(file_path) as img:
            img.verify()  # This will raise an exception if the image is corrupted
            
        # Re-open to check dimensions (verify() closes the image)
        with Image.open(file_path) as img:
            if img.size[0] <= 0 or img.size[1] <= 0:
                print(f"Image has invalid dimensions: {img.size}")
                return False
                
        return True
        
    except (UnidentifiedImageError, OSError, ValueError) as e:
        print(f"Invalid or corrupted image file {file_path}: {e}")
        return False
    except Exception as e:
        print(f"Unexpected error validating image {file_path}: {e}")
        return False


def safe_remove_file(file_path: Optional[str]) -> None:
    """
    Safely remove a file without raising exceptions.
    
    Args:
        file_path: Path to the file to remove
    """
    if file_path and os.path.exists(file_path):
        try:
            os.remove(file_path)
        except OSError as e:
            print(f"Error removing file {file_path}: {e}")
