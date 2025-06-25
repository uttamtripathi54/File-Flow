import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import queue
# Import only the class names here
from src.core.organizer import FileOrganizer
from src.core.log_manager import LogManager # Import LogManager class for type hinting
from src.core.notification_manager import NotificationManager # Import NotificationManager class for type hinting
from src.config.settings import SettingsManager
from src.gui.preview_dialog import PreviewDialog # Import the PreviewDialog

class MainWindow(tk.Tk):
    """
    The main Tkinter application window for the File Organizer.
    Handles user interaction, displays progress, and integrates with backend logic.
    """
    # Accept manager instances as arguments
    def __init__(self, settings_manager: SettingsManager, app_log_manager: LogManager, app_notification_manager: NotificationManager):
        super().__init__()
        self.title("Super Smart File Organizer")
        self.geometry("700x550")
        self.resizable(False, False) # Fixed size for simplicity

        # Assign the passed manager instances
        self.settings_manager = settings_manager
        self.app_log_manager = app_log_manager
        self.app_notification_manager = app_notification_manager

        self.log_queue = self.app_log_manager.get_queue() # Get the queue for UI updates
        # Pass the log and notification managers to FileOrganizer
        self.file_organizer = FileOrganizer(self.log_queue, self.settings_manager, self.app_log_manager, self.app_notification_manager)

        self._create_widgets()
        self._load_saved_settings()

        # Start checking the log queue for updates
        self.after(100, self._check_log_queue)

    def _create_widgets(self):
        """Creates and lays out all widgets in the main window."""
        # Configure grid for main window
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        # Main Frame
        main_frame = ttk.Frame(self, padding="15")
        main_frame.grid(row=0, column=0, sticky="nsew")
        main_frame.columnconfigure(0, weight=1) # Allow content to expand

        # Source Directory Selection
        ttk.Label(main_frame, text="Source Directory:").grid(row=0, column=0, sticky="w", pady=(0, 2))
        source_frame = ttk.Frame(main_frame)
        source_frame.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        source_frame.columnconfigure(0, weight=1)
        self.source_dir_entry = ttk.Entry(source_frame, width=50)
        self.source_dir_entry.grid(row=0, column=0, sticky="ew")
        ttk.Button(source_frame, text="Browse", command=self._browse_source_dir).grid(row=0, column=1, padx=(5, 0))

        # Destination Directory Selection
        ttk.Label(main_frame, text="Destination Directory:").grid(row=2, column=0, sticky="w", pady=(0, 2))
        dest_frame = ttk.Frame(main_frame)
        dest_frame.grid(row=3, column=0, sticky="ew", pady=(0, 10))
        dest_frame.columnconfigure(0, weight=1)
        self.destination_dir_entry = ttk.Entry(dest_frame, width=50)
        self.destination_dir_entry.grid(row=0, column=0, sticky="ew")
        ttk.Button(dest_frame, text="Browse", command=self._browse_destination_dir).grid(row=0, column=1, padx=(5, 0))

        # Duplicate Handling Option
        ttk.Label(main_frame, text="Duplicate Handling:").grid(row=4, column=0, sticky="w", pady=(0, 2))
        self.duplicate_handling_var = tk.StringVar(value="rename") # Default to 'rename'
        duplicate_frame = ttk.Frame(main_frame)
        duplicate_frame.grid(row=5, column=0, sticky="w", pady=(0, 10))
        ttk.Radiobutton(duplicate_frame, text="Rename new file", variable=self.duplicate_handling_var, value="rename").pack(side="left", padx=(0, 10))
        ttk.Radiobutton(duplicate_frame, text="Skip existing file", variable=self.duplicate_handling_var, value="skip").pack(side="left")

        # Sort by Date Option
        ttk.Label(main_frame, text="Sort by Date:").grid(row=6, column=0, sticky="w", pady=(0, 2))
        self.sort_by_date_var = tk.StringVar(value="None")
        sort_by_date_options = ["None", "Year", "Year-Month", "Year-Month-Day"]
        ttk.OptionMenu(main_frame, self.sort_by_date_var, self.sort_by_date_var.get(), *sort_by_date_options).grid(row=7, column=0, sticky="w", pady=(0, 10))


        # Control Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=8, column=0, sticky="ew", pady=(10, 0))
        button_frame.columnconfigure(0, weight=1)
        button_frame.columnconfigure(1, weight=1)
        button_frame.columnconfigure(2, weight=1)

        self.preview_button = ttk.Button(button_frame, text="Preview Actions", command=self._start_preview)
        self.preview_button.grid(row=0, column=0, sticky="ew", padx=(0, 5))

        self.organize_button = ttk.Button(button_frame, text="Organize Files", command=self._start_organize)
        self.organize_button.grid(row=0, column=1, sticky="ew", padx=(5, 5))

        self.stop_button = ttk.Button(button_frame, text="Stop", command=self._stop_organize, state="disabled")
        self.stop_button.grid(row=0, column=2, sticky="ew", padx=(5, 0))

        # Progress Bar and Status
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(main_frame, orient="horizontal", length=400, mode="determinate", variable=self.progress_var)
        self.progress_bar.grid(row=9, column=0, sticky="ew", pady=(10, 5))

        self.status_label = ttk.Label(main_frame, text="Ready.")
        self.status_label.grid(row=10, column=0, sticky="w", pady=(0, 10))

        # Log Display Area
        ttk.Label(main_frame, text="Activity Log:").grid(row=11, column=0, sticky="w", pady=(0, 2))
        log_frame = ttk.Frame(main_frame)
        log_frame.grid(row=12, column=0, sticky="nsew")
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)

        self.log_text = tk.Text(log_frame, wrap="word", height=10, width=60, state="disabled", font=('TkFixedFont', 9))
        self.log_text.grid(row=0, column=0, sticky="nsew")

        log_scrollbar = ttk.Scrollbar(log_frame, orient="vertical", command=self.log_text.yview)
        log_scrollbar.grid(row=0, column=1, sticky="ns")
        self.log_text.config(yscrollcommand=log_scrollbar.set)

    def _load_saved_settings(self):
        """Loads and applies saved settings from SettingsManager."""
        self.source_dir_entry.insert(0, self.settings_manager.get("default_source_dir"))
        self.destination_dir_entry.insert(0, self.settings_manager.get("default_destination_dir"))
        self.duplicate_handling_var.set(self.settings_manager.get("duplicate_handling"))
        self.sort_by_date_var.set(self.settings_manager.get("sort_by_date_format"))
        # No need to set notification_manager.enabled here, it's set at init based on settings

    def _save_current_settings(self):
        """Saves current GUI settings to the SettingsManager."""
        self.settings_manager.set("default_source_dir", self.source_dir_entry.get())
        self.settings_manager.set("default_destination_dir", self.destination_dir_entry.get())
        self.settings_manager.set("duplicate_handling", self.duplicate_handling_var.get())
        self.settings_manager.set("sort_by_date_format", self.sort_by_date_var.get())
        # enable_desktop_notifications is assumed to be handled in a separate settings dialog if added

    def _browse_source_dir(self):
        """Opens a dialog to select the source directory."""
        folder_selected = filedialog.askdirectory()
        if folder_selected:
            self.source_dir_entry.delete(0, tk.END)
            self.source_dir_entry.insert(0, folder_selected)
            self._save_current_settings() # Save selection as default

    def _browse_destination_dir(self):
        """Opens a dialog to select the destination directory."""
        folder_selected = filedialog.askdirectory()
        if folder_selected:
            self.destination_dir_entry.delete(0, tk.END)
            self.destination_dir_entry.insert(0, folder_selected)
            self._save_current_settings() # Save selection as default

    def _validate_paths(self, source_dir, destination_dir):
        """Validates source and destination directories."""
        if not source_dir:
            messagebox.showwarning("Input Error", "Please select a source directory.")
            return False
        if not os.path.isdir(source_dir):
            messagebox.showwarning("Input Error", "Source directory does not exist or is not a valid directory.")
            return False
        if not destination_dir:
            messagebox.showwarning("Input Error", "Please select a destination directory.")
            return False
        # Destination directory will be created if it doesn't exist by organizer.py,
        # so we only check if the *parent* exists or if it's a valid path format.
        return True

    def _start_preview(self):
        """Initiates the file organization in preview mode."""
        source_dir = self.source_dir_entry.get()
        destination_dir = self.destination_dir_entry.get()
        duplicate_handling = self.duplicate_handling_var.get()
        sort_by_date_format = self.sort_by_date_var.get()

        if not self._validate_paths(source_dir, destination_dir):
            return

        self._set_ui_busy(True)
        self.status_label.config(text="Generating preview...")
        self.progress_bar.config(mode="indeterminate") # Indeterminate for preview
        self.progress_bar.start()

        self.log_text.config(state="normal")
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state="disabled")

        self.file_organizer.organize_files_threaded(
            source_dir, destination_dir, duplicate_handling, sort_by_date_format, preview_mode=True
        )

    def _start_organize(self):
        """Initiates the actual file organization process."""
        source_dir = self.source_dir_entry.get()
        destination_dir = self.destination_dir_entry.get()
        duplicate_handling = self.duplicate_handling_var.get()
        sort_by_date_format = self.sort_by_date_var.get()

        if not self._validate_paths(source_dir, destination_dir):
            return

        confirm = messagebox.askyesno(
            "Confirm Organization",
            f"Are you sure you want to organize files from:\n'{source_dir}'\nTo:\n'{destination_dir}'\n\nThis action will move files. Continue?"
        )
        if not confirm:
            self.status_label.config(text="Organization cancelled by user.")
            return

        self._set_ui_busy(True)
        self.status_label.config(text="Starting organization...")
        self.progress_bar.config(mode="determinate") # Determinate for actual progress
        self.progress_var.set(0) # Reset progress

        self.log_text.config(state="normal")
        self.log_text.delete(1.0, tk.END) # Clear previous logs
        self.log_text.config(state="disabled")

        self.file_organizer.organize_files_threaded(
            source_dir, destination_dir, duplicate_handling, sort_by_date_format, preview_mode=False
        )

    def _stop_organize(self):
        """Sends a stop signal to the file organizer thread."""
        self.file_organizer.stop()
        self._set_ui_busy(False) # UI becomes responsive immediately after stop signal
        self.status_label.config(text="Stopping organization...")

    def _set_ui_busy(self, is_busy):
        """Enables/disables UI elements based on busy status."""
        state = "disabled" if is_busy else "normal"
        self.source_dir_entry.config(state=state)
        self.destination_dir_entry.config(state=state)
        self.preview_button.config(state=state)
        self.organize_button.config(state=state)
        self.stop_button.config(state="normal" if is_busy else "disabled")
        # To truly disable radio buttons, you'd iterate through their parent frame's children
        # or store references to them. For simplicity in this example, we don't disable them directly.

    def _check_log_queue(self):
        """
        Periodically checks the log queue for messages from the organizer thread
        and updates the GUI.
        """
        while True:
            try:
                message_item = self.log_queue.get_nowait()
                msg_type = message_item.get("type")

                if msg_type == "log":
                    message = message_item.get("message")
                    self.log_text.config(state="normal")
                    self.log_text.insert(tk.END, message + "\n")
                    self.log_text.see(tk.END) # Auto-scroll to bottom
                    self.log_text.config(state="disabled")
                elif msg_type == "progress":
                    current = message_item.get("current")
                    total = message_item.get("total")
                    status_message = message_item.get("message", "")

                    if total > 0:
                        progress_value = (current / total) * 100
                        self.progress_var.set(progress_value)
                        self.status_label.config(text=f"{status_message} ({current}/{total})")
                    else:
                        self.progress_var.set(0)
                        self.status_label.config(text=status_message)

                    if current == total: # Process finished
                        self._set_ui_busy(False)
                        self.progress_bar.stop()
                        if not status_message: self.status_label.config(text="Ready.")

                elif msg_type == "preview_results":
                    actions = message_item.get("actions", [])
                    preview_dialog = PreviewDialog(self, actions)
                    preview_dialog.grab_set() # Make it modal
                    self.wait_window(preview_dialog)
                    self._set_ui_busy(False)
                    self.progress_bar.stop()
                    self.status_label.config(text="Preview ready.")

            except queue.Empty:
                break # No more messages in the queue for now
            except Exception as e:
                # Log to console if something goes wrong with processing queue messages
                print(f"Error processing GUI queue message: {e}")
                self._set_ui_busy(False) # Attempt to unfreeze UI
                self.progress_bar.stop()
                break # Stop processing to avoid infinite loop on error

        self.after(100, self._check_log_queue) # Check again after 100ms