"""
Git Auto Commit - GUI Interface
Provides a Tkinter GUI for managing Git Auto Commit
"""
import os
import sys
import ttkbootstrap as tb
from ttkbootstrap.constants import *
from tkinter import ttk, filedialog, messagebox
import threading
import logging
from tkinter import PhotoImage
import json
from ttkbootstrap.tooltip import ToolTip

from .config import Config
from .utils import commit_and_push, is_git_repo, git_init_and_first_commit, setup_systemd_user_service
from .watcher import Watcher

logger = logging.getLogger(__name__)

class GitAutoCommitGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Git Auto Commit")
        self.root.geometry("900x600")
        self.root.minsize(800, 500)
        default_font = ("Segoe UI", 12)
        self.root.option_add("*Font", default_font)
        self.current_theme = "darkly"
        self.config = Config()
        self.watcher = Watcher()
        self.watcher_thread = None
        self.status_var = tb.StringVar(value="Ready.")
        self.setup_ui()
        self.refresh_folder_list()
        
    def toggle_dark_mode(self):
        # Switch between darkly and flatly themes
        new_theme = "flatly" if self.current_theme == "darkly" else "darkly"
        self.root.style.theme_use(new_theme)
        self.current_theme = new_theme

    def setup_ui(self):
        """Setup the UI components"""
        main_frame = ttk.Frame(self.root, padding="16")
        main_frame.pack(fill=tb.BOTH, expand=True)
        topbar = ttk.Frame(main_frame)
        topbar.pack(fill=tb.X, pady=(0, 8))
        dark_btn = ttk.Button(topbar, text="🌙 Toggle Dark Mode", command=self.toggle_dark_mode, style="primary.TButton")
        dark_btn.pack(side=tb.RIGHT, padx=12, pady=6)
        ToolTip(dark_btn, text="Switch between dark and light mode")
        settings_btn = ttk.Button(topbar, text="⚙️ Settings", command=self.open_settings_dialog, style="secondary.TButton")
        settings_btn.pack(side=tb.RIGHT, padx=12, pady=6)
        ToolTip(settings_btn, text="Open settings and preferences")
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill=tb.BOTH, expand=True)
        register_frame = ttk.Frame(notebook, padding="16")
        notebook.add(register_frame, text="Register Folder")
        self.setup_register_tab(register_frame)
        manage_frame = ttk.Frame(notebook, padding="16")
        notebook.add(manage_frame, text="Manage Folders")
        self.setup_manage_tab(manage_frame)
        status_bar = ttk.Frame(self.root)
        status_bar.pack(side=tb.BOTTOM, fill=tb.X)
        status_label = ttk.Label(status_bar, textvariable=self.status_var, anchor="w")
        status_label.pack(side=tb.LEFT, fill=tb.X, expand=True, padx=12, pady=4)
        
    def setup_register_tab(self, parent):
        """Setup the register tab UI"""
        # Folder selection frame
        folder_frame = ttk.Frame(parent)
        folder_frame.pack(fill=tb.X, padx=5, pady=5)
        
        ttk.Label(folder_frame, text="Local Folder:").pack(side=tb.LEFT, padx=5)
        self.folder_var = tb.StringVar()
        folder_entry = ttk.Entry(folder_frame, textvariable=self.folder_var, width=40, style="info.TEntry")
        folder_entry.pack(side=tb.LEFT, fill=tb.X, expand=True, padx=8, pady=4)
        ToolTip(folder_entry, text="Path to the local folder you want to track")
        
        browse_btn = ttk.Button(folder_frame, text="📂 Browse", command=self.browse_folder, style="success.TButton")
        browse_btn.pack(side=tb.RIGHT, padx=8, pady=4)
        ToolTip(browse_btn, text="Browse for a folder on your system")
        
        # Repository URL frame
        repo_frame = ttk.Frame(parent)
        repo_frame.pack(fill=tb.X, padx=5, pady=5)
        
        ttk.Label(repo_frame, text="GitHub URL:").pack(side=tb.LEFT, padx=5)
        self.repo_var = tb.StringVar()
        repo_entry = ttk.Entry(repo_frame, textvariable=self.repo_var, width=50, style="info.TEntry")
        repo_entry.pack(side=tb.LEFT, fill=tb.X, expand=True, padx=8, pady=4)
        ToolTip(repo_entry, text="GitHub repository URL (e.g. https://github.com/user/repo.git)")
        
        # Username frame
        username_frame = ttk.Frame(parent)
        username_frame.pack(fill=tb.X, padx=5, pady=5)
        
        ttk.Label(username_frame, text="Username:").pack(side=tb.LEFT, padx=5)
        self.username_var = tb.StringVar()
        username_entry = ttk.Entry(username_frame, textvariable=self.username_var, width=30, style="info.TEntry")
        username_entry.pack(side=tb.LEFT, fill=tb.X, expand=True, padx=8, pady=4)
        ToolTip(username_entry, text="Your GitHub username")
        
        # Token frame
        token_frame = ttk.Frame(parent)
        token_frame.pack(fill=tb.X, padx=5, pady=5)
        
        ttk.Label(token_frame, text="GitHub Token:").pack(side=tb.LEFT, padx=5)
        self.token_var = tb.StringVar()
        token_entry = ttk.Entry(token_frame, textvariable=self.token_var, width=50, show="*", style="info.TEntry")
        token_entry.pack(side=tb.LEFT, fill=tb.X, expand=True, padx=8, pady=4)
        ToolTip(token_entry, text="Your GitHub personal access token")
        
        # Register button
        register_btn = ttk.Button(parent, text="➕ Register Folder", command=self.register_folder, style="primary.TButton")
        register_btn.pack(pady=12)
        ToolTip(register_btn, text="Register this folder for auto-commit and push")
        
    def setup_manage_tab(self, parent):
        """Setup the manage tab UI"""
        ttk.Label(parent, text="Registered Folders:").pack(anchor=tb.W, padx=5, pady=5)
        
        # Search/filter box
        search_frame = ttk.Frame(parent)
        search_frame.pack(fill=tb.X, padx=5, pady=(0, 5))
        ttk.Label(search_frame, text="Search:").pack(side=tb.LEFT)
        self.search_var = tb.StringVar()
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=40)
        search_entry.pack(side=tb.LEFT, fill=tb.X, expand=True, padx=5)
        self.search_var.trace_add('write', lambda *args: self.refresh_folder_list())
        
        # Create treeview for folder list
        columns = ("Folder", "Repository", "Watched", "Auto-Commit")
        self.folder_tree = ttk.Treeview(parent, columns=columns, show="headings", height=10)
        
        # Define headings
        self.folder_tree.heading("Folder", text="Folder")
        self.folder_tree.heading("Repository", text="Repository")
        self.folder_tree.heading("Watched", text="Watched")
        self.folder_tree.heading("Auto-Commit", text="Auto-Commit")
        
        # Define column widths and make resizable
        self.folder_tree.column("Folder", width=300, stretch=True)
        self.folder_tree.column("Repository", width=300, stretch=True)
        self.folder_tree.column("Watched", width=80, anchor="center", stretch=False)
        self.folder_tree.column("Auto-Commit", width=100, anchor="center", stretch=False)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(parent, orient=tb.VERTICAL, command=self.folder_tree.yview)
        self.folder_tree.configure(yscroll=scrollbar.set)
        
        # Pack the treeview and scrollbar
        self.folder_tree.pack(fill=tb.BOTH, expand=True, padx=5, pady=5, side=tb.LEFT)
        scrollbar.pack(side=tb.RIGHT, fill=tb.Y)
        
        # Commit history panel
        history_frame = ttk.Frame(parent)
        history_frame.pack(fill=tb.X, padx=5, pady=(0, 5))
        ttk.Label(history_frame, text="Recent Commits:").pack(anchor=tb.W)
        self.commit_history = tb.Text(history_frame, height=6, state="disabled", wrap="word")
        self.commit_history.pack(fill=tb.X, padx=2, pady=2)
        
        self.folder_tree.bind("<<TreeviewSelect>>", self.update_commit_history)
        
        # Create button frame
        button_frame = ttk.Frame(parent)
        button_frame.pack(fill=tb.X, padx=5, pady=5)
        
        # Add buttons with icons
        commit_btn = ttk.Button(button_frame, text="💾 Commit Selected", command=self.commit_selected, style="success.TButton")
        commit_btn.pack(side=tb.LEFT, padx=8, pady=4)
        ToolTip(commit_btn, text="Commit and push changes for the selected folder")
        
        edit_btn = ttk.Button(button_frame, text="✏️ Edit Selected", command=self.edit_selected, style="info.TButton")
        edit_btn.pack(side=tb.LEFT, padx=8, pady=4)
        ToolTip(edit_btn, text="Edit the configuration for the selected folder")
        
        remove_btn = ttk.Button(button_frame, text="❌ Remove Selected", command=self.remove_selected, style="danger.TButton")
        remove_btn.pack(side=tb.LEFT, padx=8, pady=4)
        ToolTip(remove_btn, text="Remove the selected folder from tracking")
        
        refresh_btn = ttk.Button(button_frame, text="🔄 Refresh List", command=self.refresh_folder_list, style="secondary.TButton")
        refresh_btn.pack(side=tb.LEFT, padx=8, pady=4)
        ToolTip(refresh_btn, text="Refresh the list of registered folders")
        
        # Watcher control frame
        watcher_frame = ttk.Frame(parent)
        watcher_frame.pack(fill=tb.X, padx=5, pady=10)
        
        # Watcher status label
        self.watcher_status_var = tb.StringVar(value="Watcher: Not Running")
        status_label = ttk.Label(watcher_frame, textvariable=self.watcher_status_var)
        status_label.pack(side=tb.LEFT, padx=5)
        
        # Add watcher control buttons
        self.start_watcher_btn = ttk.Button(watcher_frame, text="▶️ Start Watcher", command=self.start_watcher, style="success.TButton")
        self.start_watcher_btn.pack(side=tb.LEFT, padx=8, pady=4)
        ToolTip(self.start_watcher_btn, text="Start the background watcher for auto-commit")
        
        self.stop_watcher_btn = ttk.Button(watcher_frame, text="⏹️ Stop Watcher", command=self.stop_watcher, style="danger.TButton")
        self.stop_watcher_btn.pack(side=tb.LEFT, padx=8, pady=4)
        ToolTip(self.stop_watcher_btn, text="Stop the background watcher")
        self.stop_watcher_btn.config(state=tb.DISABLED)
        
        # Right-click context menu
        self.tree_menu = tb.Menu(self.root, tearoff=0)
        self.tree_menu.add_command(label="Edit", command=self.edit_selected)
        self.tree_menu.add_command(label="Remove", command=self.remove_selected)
        self.folder_tree.bind("<Button-3>", self.show_tree_menu)
        
    def browse_folder(self):
        """Open folder browser dialog"""
        folder = filedialog.askdirectory(title="Select Folder")
        if folder:
            self.folder_var.set(folder)
            
    def register_folder(self):
        """Register a new folder"""
        folder = self.folder_var.get()
        repo_url = self.repo_var.get()
        username = self.username_var.get()
        token = self.token_var.get()
        
        # Validate inputs
        if not folder or not repo_url or not username or not token:
            messagebox.showerror("Error", "All fields are required")
            return
            
        # Check if folder exists
        if not os.path.isdir(folder):
            messagebox.showerror("Error", f"Folder '{folder}' does not exist")
            return
            
        # Check if folder is a git repository
        if not is_git_repo(folder):
            if messagebox.askyesno("Git Init", f"Folder '{folder}' is not a git repository. Initialize and push initial commit?"):
                success, msg = git_init_and_first_commit(folder, repo_url, username, token)
                if not success:
                    messagebox.showerror("Error", msg)
                    return
                else:
                    messagebox.showinfo("Success", msg)
            else:
                return
        
        # Register the folder
        success = self.config.add_folder(folder, repo_url, username, token)
        
        if success:
            messagebox.showinfo("Success", f"Successfully registered folder: {folder}")
            try:
                setup_systemd_user_service()
                messagebox.showinfo("Watcher Enabled", "Watcher service enabled: will run in background and auto-start on login.")
            except Exception as e:
                messagebox.showwarning("Watcher Setup", f"Could not set up watcher service: {e}")
            # Clear form fields
            self.folder_var.set("")
            self.repo_var.set("")
            
            # Refresh folder list
            self.refresh_folder_list()
        else:
            messagebox.showerror("Error", f"Failed to register folder: {folder}")
            
    def refresh_folder_list(self):
        """Refresh the folder list in the treeview"""
        # Clear existing items
        for item in self.folder_tree.get_children():
            self.folder_tree.delete(item)
            
        # Load folders from config
        folders = self.config.get_folders()
        # Apply search filter
        query = self.search_var.get().strip().lower() if hasattr(self, 'search_var') else ''
        filtered = {}
        for folder, repo_config in folders.items():
            if not query or query in folder.lower() or query in repo_config.get('repo_url', '').lower():
                filtered[folder] = repo_config
        folders = filtered
        
        # Add folders to treeview
        for folder, repo_config in folders.items():
            # Watched status: check if watcher is running and this folder is being watched
            watched = "✅" if self.watcher.is_running() and folder in self.watcher.observers else "❌"
            # Auto-commit status: get from config, default True
            auto_commit = repo_config.get("auto_commit", True)
            auto_commit_str = "✅" if auto_commit else "❌"
            self.folder_tree.insert("", tb.END, values=(folder, repo_config["repo_url"], watched, auto_commit_str), iid=folder)
        # Add a binding for double-click on the Auto-Commit column to toggle
        self.folder_tree.bind("<Double-1>", self.on_treeview_double_click)
        
        # Optionally update commit history if a folder is selected
        self.update_commit_history()
        
    def commit_selected(self):
        """Commit the selected folder"""
        selected = self.folder_tree.selection()
        if not selected:
            messagebox.showinfo("Info", "No folder selected")
            return
            
        folder = selected[0]
        repo_config = self.config.get_folder_config(folder)
        
        if not repo_config:
            messagebox.showerror("Error", f"Folder configuration not found for {folder}")
            return
            
        success, message = commit_and_push(folder, repo_config)
        
        if success:
            messagebox.showinfo("Success", message)
        else:
            messagebox.showerror("Error", message)
            
    def remove_selected(self):
        """Remove the selected folder from tracking"""
        selected = self.folder_tree.selection()
        if not selected:
            messagebox.showinfo("Info", "No folder selected")
            return
            
        folder = selected[0]
        
        # Confirm removal
        if not messagebox.askyesno("Confirm", f"Remove folder '{folder}' from tracking?"):
            return
            
        success = self.config.remove_folder(folder)
        
        if success:
            messagebox.showinfo("Success", f"Removed folder '{folder}' from tracking")
            self.refresh_folder_list()
        else:
            messagebox.showerror("Error", f"Failed to remove folder '{folder}'")
            
    def start_watcher(self):
        """Start the watcher thread"""
        if self.watcher_thread and self.watcher_thread.is_alive():
            messagebox.showinfo("Info", "Watcher is already running")
            return
            
        # Create and start the watcher thread
        self.watcher_thread = threading.Thread(target=self.run_watcher, daemon=True)
        self.watcher_thread.start()
        
        # Update UI
        self.watcher_status_var.set("Watcher: Running")
        self.start_watcher_btn.config(state=tb.DISABLED)
        self.stop_watcher_btn.config(state=tb.NORMAL)
        
    def stop_watcher(self):
        """Stop the watcher thread"""
        if not self.watcher_thread or not self.watcher_thread.is_alive():
            messagebox.showinfo("Info", "Watcher is not running")
            return
            
        # Stop the watcher
        self.watcher.stop_watching()
        
        # Wait for the thread to finish
        self.watcher_thread.join(timeout=1.0)
        
        # Update UI
        self.watcher_status_var.set("Watcher: Not Running")
        self.start_watcher_btn.config(state=tb.NORMAL)
        self.stop_watcher_btn.config(state=tb.DISABLED)
        
    def run_watcher(self):
        """Run the watcher in a separate thread"""
        try:
            self.watcher.start_watching()
            
            # Keep the thread alive while the watcher is running
            while self.watcher.is_running():
                import time
                time.sleep(1)
                
        except Exception as e:
            logger.error(f"Error in watcher thread: {e}")
            
            # Update UI from main thread
            self.root.after(0, self.on_watcher_error, str(e))
            
    def on_watcher_error(self, error_message):
        """Handle watcher errors from the main thread"""
        messagebox.showerror("Watcher Error", f"An error occurred in the watcher:\n{error_message}")
        
        # Reset UI
        self.watcher_status_var.set("Watcher: Not Running")
        self.start_watcher_btn.config(state=tb.NORMAL)
        self.stop_watcher_btn.config(state=tb.DISABLED)
        
    def on_closing(self):
        """Handle window closing"""
        if self.watcher.is_running():
            if messagebox.askyesno("Quit", "Watcher is running. Stop it and quit?"):
                self.watcher.stop_watching()
                self.root.destroy()
        else:
            self.root.destroy()

    def update_commit_history(self, event=None):
        selected = self.folder_tree.selection()
        if not selected:
            self.commit_history.config(state="normal")
            self.commit_history.delete(1.0, tb.END)
            self.commit_history.insert(tb.END, "Select a folder to view recent commits.")
            self.commit_history.config(state="disabled")
            return
        folder = selected[0]
        import subprocess
        try:
            result = subprocess.run([
                "git", "log", "-n", "5", "--pretty=format:%h %ad %s", "--date=short"
            ], cwd=folder, capture_output=True, text=True, check=True)
            log = result.stdout.strip()
            if not log:
                log = "No commits found."
        except Exception as e:
            log = f"Error reading git log: {e}"
        self.commit_history.config(state="normal")
        self.commit_history.delete(1.0, tb.END)
        self.commit_history.insert(tb.END, log)
        self.commit_history.config(state="disabled")

    def on_treeview_double_click(self, event):
        # Identify column and row
        region = self.folder_tree.identify("region", event.x, event.y)
        if region != "cell":
            return
        col = self.folder_tree.identify_column(event.x)
        row = self.folder_tree.identify_row(event.y)
        if not row:
            return
        col_num = int(col.replace("#", ""))
        # Auto-Commit is the 4th column
        if col_num == 4:
            folder = row
            repo_config = self.config.get_folder_config(folder)
            if repo_config is None:
                return
            current = repo_config.get("auto_commit", True)
            new_value = not current
            repo_config["auto_commit"] = new_value
            # Save back to config
            self.config.config["folders"][folder]["auto_commit"] = new_value
            self.config.save_config()
            self.refresh_folder_list()
            self.status_var.set(f"Auto-commit {'enabled' if new_value else 'disabled'} for {folder}")

    def edit_selected(self):
        selected = self.folder_tree.selection()
        if not selected:
            messagebox.showinfo("Info", "No folder selected")
            return
        folder = selected[0]
        repo_config = self.config.get_folder_config(folder)
        if not repo_config:
            messagebox.showerror("Error", f"Folder configuration not found for {folder}")
            return
        # Create edit dialog
        edit_win = tb.Toplevel(self.root)
        edit_win.title(f"Edit Config: {folder}")
        edit_win.geometry("500x250")
        edit_win.transient(self.root)
        edit_win.grab_set()

        tb.Label(edit_win, text="Repository URL:").pack(anchor=tb.W, padx=10, pady=(10, 0))
        repo_var = tb.StringVar(value=repo_config.get("repo_url", ""))
        tb.Entry(edit_win, textvariable=repo_var, width=60).pack(fill=tb.X, padx=10)

        tb.Label(edit_win, text="Username:").pack(anchor=tb.W, padx=10, pady=(10, 0))
        user_var = tb.StringVar(value=repo_config.get("username", ""))
        tb.Entry(edit_win, textvariable=user_var, width=40).pack(fill=tb.X, padx=10)

        tb.Label(edit_win, text="Token:").pack(anchor=tb.W, padx=10, pady=(10, 0))
        token_var = tb.StringVar(value=repo_config.get("token", ""))
        tb.Entry(edit_win, textvariable=token_var, width=60, show="*").pack(fill=tb.X, padx=10)

        def save_changes():
            repo_config["repo_url"] = repo_var.get()
            repo_config["username"] = user_var.get()
            repo_config["token"] = token_var.get()
            self.config.config["folders"][folder] = repo_config
            self.config.save_config()
            self.refresh_folder_list()
            self.status_var.set(f"Updated config for {folder}")
            edit_win.destroy()

        btn_frame = ttk.Frame(edit_win)
        btn_frame.pack(pady=15)
        ttk.Button(btn_frame, text="Save", command=save_changes).pack(side=tb.LEFT, padx=10)
        ttk.Button(btn_frame, text="Cancel", command=edit_win.destroy).pack(side=tb.LEFT, padx=10)

    def open_settings_dialog(self):
        prefs_path = os.path.expanduser("~/.gac/gui_prefs.json")
        # Load existing prefs
        prefs = {}
        if os.path.exists(prefs_path):
            try:
                with open(prefs_path, "r") as f:
                    prefs = json.load(f)
            except Exception:
                pass
        # Dialog
        win = tb.Toplevel(self.root)
        win.title("Settings / Preferences")
        win.geometry("400x250")
        win.transient(self.root)
        win.grab_set()

        # Dark mode toggle
        dark_var = tb.BooleanVar(value=self.current_theme == "darkly")
        dark_chk = ttk.Checkbutton(win, text="Enable Dark Mode", variable=dark_var)
        dark_chk.pack(anchor=tb.W, padx=20, pady=10)

        # Watcher debounce time
        tb.Label(win, text="Watcher Debounce Time (seconds):").pack(anchor=tb.W, padx=20, pady=(10, 0))
        debounce_var = tb.StringVar(value=str(prefs.get("debounce", 30)))
        tb.Entry(win, textvariable=debounce_var, width=10).pack(anchor=tb.W, padx=20)

        # Language (placeholder)
        tb.Label(win, text="Language (coming soon):").pack(anchor=tb.W, padx=20, pady=(10, 0))
        lang_var = tb.StringVar(value=prefs.get("lang", "en"))
        lang_entry = ttk.Combobox(win, textvariable=lang_var, values=["en", "es", "fr", "de"], state="readonly")
        lang_entry.pack(anchor=tb.W, padx=20)

        def save_prefs():
            prefs["dark_mode"] = self.current_theme == "darkly"
            prefs["debounce"] = int(debounce_var.get()) if debounce_var.get().isdigit() else 30
            prefs["lang"] = lang_var.get()
            with open(prefs_path, "w") as f:
                json.dump(prefs, f, indent=2)
            # Apply dark mode live
            if self.current_theme != ("darkly" if dark_var.get() else "flatly"):
                self.current_theme = "darkly" if dark_var.get() else "flatly"
                self.root.style.theme_use(self.current_theme)
            self.status_var.set("Preferences saved.")
            win.destroy()

        btn_frame = ttk.Frame(win)
        btn_frame.pack(pady=15)
        ttk.Button(btn_frame, text="Save", command=save_prefs).pack(side=tb.LEFT, padx=10)
        ttk.Button(btn_frame, text="Cancel", command=win.destroy).pack(side=tb.LEFT, padx=10)

    def show_tree_menu(self, event):
        row_id = self.folder_tree.identify_row(event.y)
        if row_id:
            self.folder_tree.selection_set(row_id)
            self.tree_menu.tk_popup(event.x_root, event.y_root)

def launch_gui():
    """Launch the GUI application"""
    root = tb.Window(themename="darkly")
    app = GitAutoCommitGUI(root)
    
    # Set window close handler
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    
    # Start the main loop
    root.mainloop()