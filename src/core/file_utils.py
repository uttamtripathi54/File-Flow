import os
from datetime import datetime
from PIL import Image # For EXIF data (requires Pillow)

# IMPORTANT: _global_log_manager_instance will be set by app.py.
# This makes sure the instance created in app.py is accessible here.
_global_log_manager_instance = None # Private internal placeholder

def set_global_log_manager(instance):
    """Sets the global log manager instance for this module."""
    global _global_log_manager_instance
    _global_log_manager_instance = instance

def get_log_manager():
    """Retrieves the global log manager instance."""
    if _global_log_manager_instance is None:
        # Fallback for direct testing or unexpected paths, though app.py should set it
        # This block should ideally not be hit during normal app execution.
        print("Warning: Global log_manager not set. Creating a temporary one in file_utils.")
        from src.core.log_manager import LogManager # Import class for fallback
        temp_log = LogManager(log_file_path="fallback_log.txt")
        set_global_log_manager(temp_log)
    return _global_log_manager_instance


# --- Original file_utils content below, updated to use get_log_manager() ---

def get_file_extension(filename):
    """Returns the lowercase extension of a file."""
    # os.path.splitext returns a tuple ('filename', '.ext')
    return os.path.splitext(filename)[1].lower()

def get_file_creation_or_modification_date(file_path, use_creation_date=True):
    """
    Returns the file's creation date (c_time) or modification date (m_time) as a datetime object.
    Falls back to modification date if creation date is not reliably available on all OS.
    """
    try:
        if use_creation_date:
            timestamp = os.path.getctime(file_path)
        else:
            timestamp = os.path.getmtime(file_path)
        return datetime.fromtimestamp(timestamp)
    except Exception as e:
        get_log_manager().warning(f"Could not get date for '{file_path}': {e}. Using current date as fallback.")
        return datetime.now() # Fallback

def get_exif_date_taken(image_path):
    """
    Attempts to extract the original date taken from an image's EXIF data.
    Requires Pillow library. Returns datetime object or None if not found/error.
    """
    try:
        with Image.open(image_path) as img:
            # Get EXIF data if available, or return None
            exif_data = img._getexif()
            if exif_data:
                # 36867 is the tag for DateTimeOriginal (EXIF spec)
                if 36867 in exif_data:
                    date_str = exif_data[36867]
                    # EXIF date format is "YYYY:MM:DD HH:MM:SS"
                    return datetime.strptime(date_str, '%Y:%m:%d %H:%M:%S')
    except Exception as e:
        # Catch various PIL/Pillow errors (e.g., not an image, corrupted EXIF)
        get_log_manager().warning(f"Could not extract EXIF date from '{image_path}': {e}")
    return None

def resolve_duplicate_filepath(filepath, handling_method="rename"):
    """
    Resolves duplicate file paths based on the specified handling method.
    If 'rename', appends (n) before the extension.
    If 'skip', returns None (indicating the file should be skipped).
    """
    if not os.path.exists(filepath):
        return filepath # No duplicate, safe to use

    if handling_method == "skip":
        get_log_manager().info(f"Skipping '{os.path.basename(filepath)}' due to duplicate existing.")
        return None
    elif handling_method == "rename":
        base, ext = os.path.splitext(filepath)
        counter = 1
        new_filepath = f"{base} ({counter}){ext}"
        # Loop until a unique filename is found
        while os.path.exists(new_filepath):
            counter += 1
            new_filepath = f"{base} ({counter}){ext}"
        get_log_manager().info(f"Renaming '{os.path.basename(filepath)}' to '{os.path.basename(new_filepath)}' due to duplicate.")
        return new_filepath
    else:
        # Default to rename if handling_method is unknown or invalid
        get_log_manager().warning(f"Unknown duplicate handling method '{handling_method}'. Defaulting to 'rename'.")
        return resolve_duplicate_filepath(filepath, "rename")