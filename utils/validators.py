"""
File validation utilities for Medication Reconciliation Agent.
Validates file types and sizes for uploaded documents.
"""

from typing import Tuple

# Allowed file extensions
ALLOWED_EXTENSIONS = {
    'pdf': ['.pdf'],
    'image': ['.jpg', '.jpeg', '.png']
}

# Maximum file size: 10MB
MAX_FILE_SIZE_MB = 10
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024


def validate_file_type(filename: str) -> Tuple[bool, str]:
    """
    Validate if the uploaded file has an allowed extension.

    Args:
        filename: Name of the uploaded file

    Returns:
        Tuple of (is_valid, message)
    """
    if not filename:
        return False, "No file provided"

    # Get file extension
    file_ext = filename.lower().split('.')[-1] if '.' in filename else ''

    # Check against allowed extensions
    all_allowed = ALLOWED_EXTENSIONS['pdf'] + ALLOWED_EXTENSIONS['image']
    allowed_extensions_str = ', '.join(all_allowed)

    if f'.{file_ext}' in all_allowed:
        return True, "Valid file type"
    else:
        return False, f"Invalid file type. Allowed: {allowed_extensions_str}"


def validate_file_size(file_size: int) -> Tuple[bool, str]:
    """
    Validate if the uploaded file size is within limits.

    Args:
        file_size: Size of the file in bytes

    Returns:
        Tuple of (is_valid, message)
    """
    if file_size > MAX_FILE_SIZE_BYTES:
        return False, f"File too large. Maximum size: {MAX_FILE_SIZE_MB}MB"

    return True, "Valid file size"


def validate_upload(filename: str, file_size: int) -> Tuple[bool, str]:
    """
    Complete validation for uploaded file.

    Args:
        filename: Name of the uploaded file
        file_size: Size of the file in bytes

    Returns:
        Tuple of (is_valid, message)
    """
    # Validate file type
    type_valid, type_msg = validate_file_type(filename)
    if not type_valid:
        return False, type_msg

    # Validate file size
    size_valid, size_msg = validate_file_size(file_size)
    if not size_valid:
        return False, size_msg

    return True, "File validated successfully"
