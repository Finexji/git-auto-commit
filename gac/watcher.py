"""
Git Auto Commit - Watcher module
Uses watchdog to monitor registered folders for changes and auto-commit them
"""
import os
import time
import threading
import logging
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from .config import Config
from .utils import commit_and_push

logger = logging.getLogger(__name__)

class GitAutoCommitHandler(FileSystemEventHandler):
    def __init__(self, folder, repo_config, debounce_seconds=30):
        super().__init__()
        self.folder = folder
        self.repo_config = repo_config
        self.debounce_seconds = debounce_seconds
        self.last_modified = 0
        self.timer = None
        self.lock = threading.Lock()
        
    def on_any_event(self, event):
        # Skip events in the .git directory
        if ".git" in event.src_path:
            return
            
        # Skip directory created events to avoid duplicate commits
        if event.event_type == "created" and os.path.isdir(event.src_path):
            return
            
        logger.debug(f"Change detected in {self.folder}: {event.event_type} - {event.src_path}")
        
        with self.lock:
            # Update the last_modified timestamp
            self.last_modified = time.time()
            
            # Cancel any existing timer
            if self.timer:
                self.timer.cancel()
                
            # Create a new timer for debouncing
            self.timer = threading.Timer(self.debounce_seconds, self.commit_changes)
            self.timer.daemon = True
            self.timer.start()
            
    def commit_changes(self):
        """Commit changes after the debounce period"""
        logger.info(f"Debounce period elapsed for {self.folder}, processing changes")
        success, message = commit_and_push(self.folder, self.repo_config)
        if success:
            logger.info(f"Auto-commit successful for {self.folder}: {message}")
        else:
            logger.error(f"Auto-commit failed for {self.folder}: {message}")


class Watcher:
    def __init__(self):
        self.config = Config()
        self.observers = {}
        self.running = False
        
    def start_watching(self):
        """Start watching all registered folders"""
        if self.running:
            logger.warning("Watcher is already running")
            return True
        self.config.load_config()  # Ensure config is up to date
        folders = self.config.get_folders()
        logger.info(f"Folders loaded for watching: {folders}")
        if not folders:
            logger.warning("No folders registered for watching")
            return False
        logger.info(f"Starting to watch {len(folders)} folders")
        for folder, repo_config in folders.items():
            self.watch_folder(folder, repo_config)
        self.running = True
        return True
        
    def stop_watching(self):
        """Stop watching all folders"""
        if not self.running:
            logger.warning("Watcher is not running")
            return False
            
        logger.info("Stopping all folder watchers")
        
        for folder, observer in self.observers.items():
            logger.info(f"Stopping watcher for {folder}")
            observer.stop()
            observer.join()
            
        self.observers = {}
        self.running = False
        return True
        
    def watch_folder(self, folder, repo_config):
        """Watch a single folder for changes"""
        if folder in self.observers:
            logger.warning(f"Already watching folder {folder}")
            return False
            
        logger.info(f"Setting up watcher for {folder}")
        
        event_handler = GitAutoCommitHandler(folder, repo_config)
        observer = Observer()
        observer.schedule(event_handler, folder, recursive=True)
        observer.daemon = True
        observer.start()
        
        self.observers[folder] = observer
        logger.info(f"Started watching {folder}")
        return True
        
    def is_running(self):
        """Check if the watcher is running"""
        return self.running
        
    def run_forever(self):
        """Run the watcher in the foreground"""
        if not self.start_watching():
            return False
            
        try:
            logger.info("Watcher running in foreground. Press Ctrl+C to stop.")
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Received keyboard interrupt. Stopping watchers.")
            self.stop_watching()
        
        return True