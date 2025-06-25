import tkinter as tk
from tkinter import ttk

class PreviewDialog(tk.Toplevel):
    """
    A Toplevel window to display the proposed file organization actions in preview mode.
    """
    def __init__(self, parent, actions):
        super().__init__(parent)
        self.title("Preview Organization Actions")
        self.geometry("800x600")
        self.resizable(True, True)

        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        self.actions = actions

        self._create_widgets()
        self._populate_listbox()

    def _create_widgets(self):
        """Creates the widgets for the preview dialog."""
        # Frame for controls and listbox
        main_frame = ttk.Frame(self, padding="10")
        main_frame.grid(row=0, column=0, sticky="nsew")
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=1) # Listbox row

        # Label
        ttk.Label(main_frame, text="Proposed Actions:").grid(row=0, column=0, sticky="nw", pady=(0, 5))

        # Scrollable Listbox
        list_frame = ttk.Frame(main_frame)
        list_frame.grid(row=1, column=0, sticky="nsew")
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)

        self.listbox = tk.Listbox(list_frame, width=100, height=20, font=('TkDefaultFont', 10))
        self.listbox.grid(row=0, column=0, sticky="nsew")

        # Scrollbars
        scrollbar_y = ttk.Scrollbar(list_frame, orient="vertical", command=self.listbox.yview)
        scrollbar_y.grid(row=0, column=1, sticky="ns")
        self.listbox.config(yscrollcommand=scrollbar_y.set)

        scrollbar_x = ttk.Scrollbar(list_frame, orient="horizontal", command=self.listbox.xview)
        scrollbar_x.grid(row=1, column=0, sticky="ew")
        self.listbox.config(xscrollcommand=scrollbar_x.set)

        # Close button
        ttk.Button(main_frame, text="Close", command=self.destroy).grid(row=2, column=0, pady=(10, 0))

    def _populate_listbox(self):
        """Populates the listbox with the action list."""
        if not self.actions:
            self.listbox.insert(tk.END, "No actions proposed in preview mode.")
            return

        for action in self.actions:
            self.listbox.insert(tk.END, action)