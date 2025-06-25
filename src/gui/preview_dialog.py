import tkinter as tk
from tkinter import ttk

class PreviewDialog(tk.Toplevel):
    """
    A Toplevel window to display the proposed file organization actions in preview mode.
    """
    def __init__(self, parent, actions):
        super().__init__(parent)
        self.title("Preview Organization Actions")
        self.geometry("900x600") # Slightly wider for action descriptions
        self.resizable(True, True)

        # Apply a consistent theme to this dialog too
        s = ttk.Style()
        s.theme_use('clam') # Or 'alt', 'default', 'vista', 'xpnative', 'aqua' (macOS)
        s.configure('TLabel', font=('Segoe UI', 10))
        s.configure('TButton', font=('Segoe UI', 10, 'bold'), padding=6)
        s.configure('TFrame', background='#f0f0f0') # Light background

        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        self.actions = actions

        self._create_widgets()
        self._populate_listbox()

        # Set focus to this new window
        self.transient(parent) # Makes it appear on top of the parent
        self.grab_set() # Disables interaction with the parent window
        self.focus_set() # Sets keyboard focus to this window
        parent.wait_window(self) # Makes the parent window wait until this one is closed

    def _create_widgets(self):
        """Creates the widgets for the preview dialog."""
        # Frame for controls and listbox
        main_frame = ttk.Frame(self, padding="15")
        main_frame.grid(row=0, column=0, sticky="nsew")
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=1) # Listbox row

        # Label
        ttk.Label(main_frame, text="Proposed Actions:").grid(row=0, column=0, sticky="nw", pady=(0, 5))

        # Scrollable Listbox (using Text widget for better display of long lines)
        list_frame = ttk.Frame(main_frame)
        list_frame.grid(row=1, column=0, sticky="nsew")
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)

        # Using Text widget for multi-line and better long text handling
        self.text_display = tk.Text(list_frame, wrap="word", height=20, width=100, state="disabled",
                                    font=('Segoe UI', 9), padx=5, pady=5, bd=2, relief="sunken")
        self.text_display.grid(row=0, column=0, sticky="nsew")

        # Scrollbars
        scrollbar_y = ttk.Scrollbar(list_frame, orient="vertical", command=self.text_display.yview)
        scrollbar_y.grid(row=0, column=1, sticky="ns")
        self.text_display.config(yscrollcommand=scrollbar_y.set)

        scrollbar_x = ttk.Scrollbar(list_frame, orient="horizontal", command=self.text_display.xview)
        scrollbar_x.grid(row=1, column=0, sticky="ew")
        self.text_display.config(xscrollcommand=scrollbar_x.set)

        # Close button
        ttk.Button(main_frame, text="Close", command=self.destroy).grid(row=2, column=0, pady=(15, 0))

    def _populate_listbox(self):
        """Populates the text_display with the action list."""
        self.text_display.config(state="normal")
        if not self.actions:
            self.text_display.insert(tk.END, "No actions proposed in preview mode.\n")
            self.text_display.insert(tk.END, "(This could mean no files were found, or all files were already organized.)\n")
        else:
            for action in self.actions:
                self.text_display.insert(tk.END, action + "\n")
        self.text_display.config(state="disabled")
        self.text_display.see(tk.END) # Scroll to bottom