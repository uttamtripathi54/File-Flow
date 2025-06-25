import os
import shutil
import threading
import queue
from src.core.file_utils import get_file_extension, get_file_creation_or_modification_date, resolve_duplicate_filepath, get_exif_date_taken
# Import manager classes for type hinting/understanding, instances are passed
from src.core.log_manager import LogManager
from src.core.notification_manager import NotificationManager


class FileOrganizer:
    """
    Core logic for organizing files. Runs in a separate thread to keep the GUI responsive.
    Communicates progress and logs back to the GUI via a queue.
    """
    # Accept explicit instances of log_manager and notification_manager
    def __init__(self, log_queue, settings, app_log_manager: LogManager, app_notification_manager: NotificationManager):
        self.log_queue = log_queue # Queue to send updates to GUI
        self.settings = settings
        self.app_log_manager = app_log_manager # Store the log manager instance
        self.app_notification_manager = app_notification_manager # Store the notification manager instance
        self._stop_event = threading.Event() # For stopping the process

    def _update_progress(self, current, total, message=""):
        """Sends progress updates to the GUI queue."""
        self.log_queue.put({"type": "progress", "current": current, "total": total, "message": message})

    def _log_message(self, level, message):
        """Logs messages using the passed app_log_manager."""
        if level == "info":
            self.app_log_manager.info(message)
        elif level == "warning":
            self.app_log_manager.warning(message)
        elif level == "error":
            self.app_log_manager.error(message)
        # The LogManager's QueueHandler automatically puts the formatted log record
        # into the log_queue, so we don't need to manually put here.

    def stop(self):
        """Sets the stop event to terminate the organization process."""
        self._stop_event.set()

    def organize_files_threaded(self, source_dir, destination_dir, duplicate_handling, sort_by_date_format, preview_mode=False):
        """
        Starts the file organization process in a new thread.
        """
        self._stop_event.clear() # Reset stop event for a new run
        thread = threading.Thread(target=self._organize_files, args=(source_dir, destination_dir, duplicate_handling, sort_by_date_format, preview_mode))
        thread.daemon = True # Allow main program to exit even if thread is running
        thread.start()

    def _organize_files(self, source_dir, destination_dir, duplicate_handling, sort_by_date_format, preview_mode):
        """
        The actual file organization logic. Runs in a separate thread.
        This now includes recursive traversal using os.walk().
        """
        # Validate paths
        if not os.path.isdir(source_dir):
            self._log_message("error", f"Source directory does not exist: '{source_dir}'")
            self.app_notification_manager.send_notification("Organizer Error", "Source directory not found!", timeout=3)
            self._update_progress(0, 0, "Error: Source directory not found.")
            return
        if not os.path.exists(destination_dir):
            try:
                os.makedirs(destination_dir)
                self._log_message("info", f"Created destination directory: '{destination_dir}'")
            except Exception as e:
                self._log_message("error", f"Could not create destination directory '{destination_dir}': {e}")
                self.app_notification_manager.send_notification("Organizer Error", "Could not create destination directory!", timeout=3)
                self._update_progress(0, 0, "Error: Could not create destination directory.")
                return
        if not os.path.isdir(destination_dir):
            self._log_message("error", f"Destination path is not a directory: '{destination_dir}'")
            self.app_notification_manager.send_notification("Organizer Error", "Destination path is not a directory!", timeout=3)
            self._update_progress(0, 0, "Error: Destination path is invalid.")
            return

        self._log_message("info", f"{'PREVIEW MODE: ' if preview_mode else ''}Starting file organization from '{source_dir}' to '{destination_dir}'...")

        all_files_to_process = []
        excluded_folders = self.settings.get_excluded_folders() # Get excluded folders from settings

        # Recursively find all files, excluding specified folders
        # Using a tuple for `dirs[:] = ...` because `dirs` is modified in-place
        for root, dirs, files in os.walk(source_dir):
            # Exclude specified folders from being traversed
            dirs[:] = [d for d in dirs if d not in excluded_folders]

            for filename in files:
                # Construct full path to file
                full_file_path = os.path.join(root, filename)
                all_files_to_process.append(full_file_path)

        total_files = len(all_files_to_process)
        files_moved = 0
        files_skipped = 0
        files_renamed = 0
        errors_count = 0
        preview_actions = []
        status_text = "" # To hold final status message

        if total_files == 0:
            status_text = "No files found to organize in the source directory or its subfolders."
            self._log_message("info", status_text)
            self.app_notification_manager.send_notification("File Organizer", status_text, timeout=3)
            self._update_progress(0, 0, status_text) # Send final update
            return

        for i, source_filepath in enumerate(all_files_to_process):
            if self._stop_event.is_set():
                status_text = "Organization process was stopped by user."
                self._log_message("warning", status_text)
                self.app_notification_manager.send_notification("Organizer Stopped", status_text, timeout=3)
                self._update_progress(i, total_files, status_text) # Send final update
                return

            # Extract just the filename for display/resolution
            filename_only = os.path.basename(source_filepath)
            self._update_progress(i, total_files, f"Processing: {filename_only}")

            try:
                file_ext = get_file_extension(filename_only)
                category_name = "Others" # Default category for unmatched files

                # Determine category based on extension
                file_categories = self.settings.get_categories()
                for category, extensions in file_categories.items():
                    if file_ext in extensions:
                        category_name = category
                        break
                # If no category matched, it remains "Others"

                target_category_dir = os.path.join(destination_dir, category_name)

                # Add date-based subfolders if enabled and not "Others"
                if sort_by_date_format != "None" and category_name != "Others":
                    file_date = None
                    if category_name == "Images":
                        # Try EXIF date first for images
                        file_date = get_exif_date_taken(source_filepath)
                    if not file_date:
                        # Fallback to modification date (or creation date, using False for mod date)
                        file_date = get_file_creation_or_modification_date(source_filepath, use_creation_date=False) # Use modification date as more reliable

                    if file_date:
                        date_folder = ""
                        if sort_by_date_format == "Year":
                            date_folder = str(file_date.year)
                        elif sort_by_date_format == "Year-Month":
                            date_folder = file_date.strftime('%Y_%m') # e.g., '2024_06'
                        elif sort_by_date_format == "Year-Month-Day":
                            date_folder = file_date.strftime('%Y_%m_%d') # e.g., '2024_06_25'

                        if date_folder:
                             target_category_dir = os.path.join(target_category_dir, date_folder)


                # Ensure the target directory exists for the current file's destination
                if not os.path.exists(target_category_dir):
                    os.makedirs(target_category_dir)
                    self._log_message("info", f"Created category directory: '{target_category_dir}'")

                destination_filepath_candidate = os.path.join(target_category_dir, filename_only)

                # Resolve duplicates for the final destination path
                final_destination_filepath = resolve_duplicate_filepath(destination_filepath_candidate, duplicate_handling)

                # Handle Preview Mode
                if preview_mode:
                    action_description = f"Move '{source_filepath}' to '{destination_filepath_candidate}'"
                    if final_destination_filepath is None: # Skipped due to duplicate
                        action_description = f"SKIP (Duplicate): '{os.path.basename(source_filepath)}' (exists at '{destination_filepath_candidate}')"
                    elif final_destination_filepath != destination_filepath_candidate: # Renamed
                        action_description = f"RENAME & Move: '{os.path.basename(source_filepath)}' to '{os.path.basename(final_destination_filepath)}'"
                    preview_actions.append(action_description)
                    continue # Skip actual file operation in preview mode

                # Perform actual file movement
                if final_destination_filepath is None: # This means it was skipped due to duplicate handling
                    files_skipped += 1
                    continue

                if final_destination_filepath != destination_filepath_candidate:
                    files_renamed += 1

                shutil.move(source_filepath, final_destination_filepath)
                files_moved += 1
                self._log_message("info", f"Moved: '{source_filepath}' to '{final_destination_filepath}'")

            except FileNotFoundError:
                errors_count += 1
                self._log_message("error", f"File not found during processing: '{source_filepath}'. It might have been moved or deleted externally. Skipping.")
            except PermissionError:
                errors_count += 1
                self._log_message("error", f"Permission denied for file: '{source_filepath}'. Skipping.")
            except shutil.Error as e: # Catch shutil specific errors (e.g., same file system, file in use, read-only)
                errors_count += 1
                self._log_message("error", f"Shutil error moving '{source_filepath}': {e}. Skipping.")
            except Exception as e:
                errors_count += 1
                self._log_message("error", f"An unexpected error occurred processing '{source_filepath}': {e}")

        # Final actions after processing all files
        if preview_mode:
            self.log_queue.put({"type": "preview_results", "actions": preview_actions})
            status_text = f"Preview complete. {len(preview_actions)} potential actions identified."
            self._log_message("info", status_text)
            self.app_notification_manager.send_notification("Preview Complete", status_text, timeout=3)
            self._update_progress(total_files, total_files, status_text) # Send final update
        else:
            status_text = f"Organization complete! Moved {files_moved} files, renamed {files_renamed} files, skipped {files_skipped} duplicates, encountered {errors_count} errors."
            self._log_message("info", status_text)
            self.app_notification_manager.send_notification("Organization Complete", status_text, timeout=5)
            self._update_progress(total_files, total_files, status_text) # Send final update