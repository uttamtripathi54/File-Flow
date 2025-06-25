import os
import shutil
import threading
import queue
# Import file_utils functions directly (they will get the global log_manager internally)
from src.core.file_utils import get_file_extension, get_file_creation_or_modification_date, resolve_duplicate_filepath, get_exif_date_taken

# Import the NotificationManager class (it will be instantiated/passed)
from src.core.log_manager import LogManager # Import class for type hinting/understanding
from src.core.notification_manager import NotificationManager # Import class for type hinting/understanding


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
        """Logs messages using the passed app_log_manager and sends to GUI queue."""
        if level == "info":
            self.app_log_manager.info(message)
        elif level == "warning":
            self.app_log_manager.warning(message)
        elif level == "error":
            self.app_log_manager.error(message)
        # The QueueHandler in LogManager already pushes to self.log_queue

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

        files_to_process = [f for f in os.listdir(source_dir) if os.path.isfile(os.path.join(source_dir, f))]
        total_files = len(files_to_process)
        files_moved = 0
        files_skipped = 0
        files_renamed = 0
        errors_count = 0
        preview_actions = []

        if total_files == 0:
            self._log_message("info", "No files found to organize in the source directory.")
            self._update_progress(0, 0, "No files found.")
            self.app_notification_manager.send_notification("File Organizer", "No files found to organize.", timeout=3)
            return

        for i, filename in enumerate(files_to_process):
            if self._stop_event.is_set():
                self._log_message("warning", "Organization process was stopped by user.")
                self.app_notification_manager.send_notification("Organizer Stopped", "File organization was interrupted.", timeout=3)
                self._update_progress(i, total_files, "Process interrupted.")
                return

            source_filepath = os.path.join(source_dir, filename)
            self._update_progress(i, total_files, f"Processing: {filename}")

            try:
                file_ext = get_file_extension(filename)
                category_name = "Others"
                file_categories = self.settings.get_categories()

                # Determine category based on extension
                for category, extensions in file_categories.items():
                    if file_ext in extensions:
                        category_name = category
                        break

                target_category_dir = os.path.join(destination_dir, category_name)

                # Add date-based subfolders if enabled
                if sort_by_date_format != "None" and category_name != "Others": # Don't date-sort 'Others'
                    file_date = None
                    if category_name == "Images":
                        # Try EXIF date first for images
                        file_date = get_exif_date_taken(source_filepath)
                    if not file_date:
                        # Fallback to creation/modification date
                        file_date = get_file_creation_or_modification_date(source_filepath)

                    if file_date:
                        if sort_by_date_format == "Year":
                            date_folder = str(file_date.year)
                        elif sort_by_date_format == "Year-Month":
                            date_folder = file_date.strftime('%Y_%m') # e.g., '2024_06'
                        elif sort_by_date_format == "Year-Month-Day":
                            date_folder = file_date.strftime('%Y_%m_%d') # e.g., '2024_06_25'
                        else:
                            date_folder = "" # Should not happen with valid options

                        if date_folder:
                             target_category_dir = os.path.join(target_category_dir, date_folder)


                # Ensure the target directory exists
                if not os.path.exists(target_category_dir):
                    os.makedirs(target_category_dir)
                    self._log_message("info", f"Created category directory: '{target_category_dir}'")

                destination_filepath = os.path.join(target_category_dir, filename)

                # Resolve duplicates
                final_destination_filepath = resolve_duplicate_filepath(destination_filepath, duplicate_handling)

                if preview_mode:
                    action_type = "Move"
                    if final_destination_filepath is None:
                        action_type = "Skip (Duplicate)"
                        preview_actions.append(f"{action_type}: '{filename}' (Source: '{source_filepath}', Destination: '{destination_filepath}')")
                    elif final_destination_filepath != destination_filepath:
                        action_type = f"Rename & Move to '{os.path.basename(final_destination_filepath)}'"
                        preview_actions.append(f"{action_type}: '{filename}' (Source: '{source_filepath}', Destination: '{final_destination_filepath}')")
                    else:
                         preview_actions.append(f"{action_type}: '{filename}' (Source: '{source_filepath}', Destination: '{final_destination_filepath}')")
                    continue # Skip actual file operation in preview mode

                if final_destination_filepath is None:
                    files_skipped += 1
                    continue # Skip the file as per duplicate handling

                if final_destination_filepath != destination_filepath:
                    files_renamed += 1

                shutil.move(source_filepath, final_destination_filepath)
                files_moved += 1
                self._log_message("info", f"Moved: '{filename}' to '{final_destination_filepath}'")

            except FileNotFoundError:
                self._log_message("error", f"File not found during processing: '{source_filepath}'")
                errors_count += 1
            except PermissionError:
                self._log_message("error", f"Permission denied for file: '{source_filepath}'. Skipping.")
                errors_count += 1
            except shutil.Error as e: # Catch shutil specific errors (e.g., same file system, file in use)
                self._log_message("error", f"Shutil error moving '{filename}': {e}. Skipping.")
                errors_count += 1
            except Exception as e:
                self._log_message("error", f"An unexpected error occurred processing '{filename}': {e}")
                errors_count += 1

        if preview_mode:
            self.log_queue.put({"type": "preview_results", "actions": preview_actions})
            self._log_message("info", f"Preview complete. {len(preview_actions)} potential actions identified.")
            self.app_notification_manager.send_notification("Preview Complete", f"Identified {len(preview_actions)} potential actions.", timeout=3)
            self.log_queue.put({"type": "progress", "current": total_files, "total": total_files, "message": "Preview Complete."})
        else:
            final_message = f"Organization complete! Moved {files_moved} files, renamed {files_renamed} files, skipped {files_skipped} duplicates, encountered {errors_count} errors."
            self._log_message("info", final_message)
            self.app_notification_manager.send_notification("Organization Complete", final_message, timeout=5)
            self._update_progress(total_files, total_files, final_message)