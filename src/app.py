# ==============================================================================
# File: src/app.py
# Description: The main entry point for the Super Smart File Organizer application.
#              Initializes the Tkinter root and starts the main window.
# ==============================================================================

import tkinter as tk
from src.gui.main_window import MainWindow
from src.core.log_manager import LogManager # Explicitly import LogManager class
from src.core.notification_manager import NotificationManager # Explicitly import NotificationManager class
from src.config.settings import SettingsManager

def main():
    """
    Main function to initialize and run the File Organizer application.
    This function is responsible for creating *single instances* of managers.
    """
    # 1. Initialize Settings Manager
    settings_manager = SettingsManager()

    # 2. Initialize Log Manager (using path from settings)
    # This creates the ONE log manager instance for the entire app
    app_log_manager = LogManager(settings_manager.get("log_file_path"))
    app_log_manager.info("Application starting...")

    # 3. Initialize Notification Manager (using setting)
    # This creates the ONE notification manager instance for the entire app
    app_notification_manager = NotificationManager(settings_manager.get("enable_desktop_notifications"))

    # Set the global log_manager instance for file_utils to use
    # This makes sure utility functions can access the main logger instance.
    from src.core.file_utils import set_global_log_manager
    set_global_log_manager(app_log_manager)

    # 4. Create and run the main GUI window, passing the initialized managers
    #    The MainWindow and other core components will now receive these instances.
    app = MainWindow(settings_manager, app_log_manager, app_notification_manager)
    app.mainloop()

    app_log_manager.info("Application closed.")


if __name__ == "__main__":
    main()