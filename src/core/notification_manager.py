try:
    from plyer import notification
except ImportError:
    print("Warning: 'plyer' library not found. Desktop notifications will be disabled.")
    print("To enable, install with: pip install plyer")
    notification = None

class NotificationManager:
    """
    Manages desktop notifications.
    Requires 'plyer' library to be installed.
    """
    def __init__(self, enabled=True):
        self.enabled = enabled

    def send_notification(self, title, message, app_name="File Organizer", timeout=5):
        """
        Sends a desktop notification if enabled and plyer is available.
        """
        if self.enabled and notification:
            try:
                notification.notify(
                    title=title,
                    message=message,
                    app_name=app_name,
                    timeout=timeout # seconds
                )
            except Exception as e:
                # Fallback print if notification fails for some reason
                print(f"Failed to send desktop notification: {e}")
                print(f"Title: {title}\nMessage: {message}")
        elif not notification:
            print(f"Notification (plyer not installed): {title} - {message}") # Console fallback

# Removed: notification_manager = None <-- THIS LINE SHOULD BE DELETED