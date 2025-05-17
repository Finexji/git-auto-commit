"""
Git Auto Commit - Command Line Interface
Provides CLI commands for managing Git Auto Commit
"""
import os
import sys
import logging
import argparse
from pathlib import Path

from .config import Config
from .utils import commit_and_push, is_git_repo, git_init_and_first_commit, setup_systemd_user_service
from .watcher import Watcher
from .gui import launch_gui as start_gui

logger = logging.getLogger(__name__)

def add_folder(args):
    """Add a folder to be tracked"""
    config = Config()
    
    # Check if the folder exists
    folder = os.path.abspath(os.path.expanduser(args.folder))
    if not os.path.isdir(folder):
        print(f"Error: Folder '{folder}' does not exist")
        return 1
        
    # Check if the folder is a git repository
    if not is_git_repo(folder):
        print(f"Folder '{folder}' is not a git repository. Initializing...")
        success, msg = git_init_and_first_commit(folder, args.repo_url, args.username, args.token)
        if not success:
            print(f"Error: {msg}")
            return 1
        print(f"{msg}")
    
    # Add the folder to config
    success = config.add_folder(folder, args.repo_url, args.username, args.token)
    
    if success:
        print(f"Successfully registered folder: {folder}")
        try:
            setup_systemd_user_service()
            print("Watcher service enabled: will run in background and auto-start on login.")
        except Exception as e:
            print(f"Warning: Could not set up watcher service: {e}")
        return 0
    else:
        print(f"Failed to register folder: {folder}")
        return 1

def list_folders(args):
    """List all tracked folders"""
    config = Config()
    folders = config.get_folders()
    
    if not folders:
        print("No folders registered for auto-commit")
        return 0
        
    print(f"Registered folders ({len(folders)}):")
    for folder, repo_config in folders.items():
        print(f"  - {folder}")
        print(f"    Repository: {repo_config['repo_url']}")
        print(f"    Username: {repo_config['username']}")
        print(f"    Token: {'*' * 8}")  # Don't show the actual token
    
    return 0

def commit_folder(args):
    """Commit and push the current folder"""
    config = Config()
    
    # Get the current directory
    current_dir = os.path.abspath(os.getcwd())
    
    if not config.is_registered_folder(current_dir):
        print(f"Error: Current folder '{current_dir}' is not registered")
        print("Use 'gac add' to register this folder first")
        return 1
        
    repo_config = config.get_folder_config(current_dir)
    
    print(f"Committing changes in {current_dir}...")
    success, message = commit_and_push(current_dir, repo_config)
    
    if success:
        print(f"Success: {message}")
        return 0
    else:
        print(f"Error: {message}")
        return 1

def start_watcher(args):
    """Start the folder watcher"""
    watcher = Watcher()
    print("Starting Git Auto Commit watcher for all registered folders...")
    success = watcher.start_watching()
    if not success:
        print("Watcher could not start (already running or no folders). Waiting...")
        try:
            import time
            while True:
                time.sleep(3600)
        except KeyboardInterrupt:
            print("\nExiting watcher.")
        return 0
    try:
        print("Watcher is running. Press Ctrl+C to stop.")
        watcher.run_forever()
    except KeyboardInterrupt:
        print("\nStopping watcher...")
        watcher.stop_watching()
    return 0

def launch_gui(args):
    """Launch the GUI interface"""
    print("Starting Git Auto Commit GUI...")
    start_gui()
    return 0

def main():
    """Main entry point for the CLI"""
    parser = argparse.ArgumentParser(
        description="Git Auto Commit - Automatically commit and push changes to GitHub"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Add folder command
    add_parser = subparsers.add_parser("add", help="Add a folder to be tracked")
    add_parser.add_argument("folder", help="Local folder path")
    add_parser.add_argument("repo_url", help="Remote GitHub repository URL")
    add_parser.add_argument("username", help="GitHub username")
    add_parser.add_argument("token", help="GitHub personal access token")
    add_parser.set_defaults(func=add_folder)
    
    # List folders command
    list_parser = subparsers.add_parser("list", help="List all tracked folders")
    list_parser.set_defaults(func=list_folders)
    
    # Commit command
    commit_parser = subparsers.add_parser("commit", help="Commit and push the current folder")
    commit_parser.set_defaults(func=commit_folder)
    
    # Start watcher command
    start_parser = subparsers.add_parser("start", help="Start the folder watcher")
    start_parser.set_defaults(func=start_watcher)
    
    # GUI command
    gui_parser = subparsers.add_parser("gui", help="Launch the GUI interface")
    gui_parser.set_defaults(func=launch_gui)
    
    # Parse arguments
    args = parser.parse_args()
    
    # If no command is given, print help
    if not args.command:
        parser.print_help()
        return 1
        
    # Execute the function for the given command
    return args.func(args)
    
if __name__ == "__main__":
    sys.exit(main())