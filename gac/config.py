"""
Git Auto Commit - Configuration module
Handles reading and writing configuration to ~/.gac/config.json
"""
import os
import json
from pathlib import Path
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

class Config:
    def __init__(self):
        self.config_dir = os.path.expanduser("~/.gac")
        self.config_file = os.path.join(self.config_dir, "config.json")
        self.ensure_config_dir()
        self.load_config()

    def ensure_config_dir(self):
        """Ensure the config directory exists"""
        if not os.path.exists(self.config_dir):
            os.makedirs(self.config_dir)
            logger.info(f"Created config directory at {self.config_dir}")

    def load_config(self):
        """Load configuration from file or create default"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    self.config = json.load(f)
                logger.info(f"Loaded configuration from {self.config_file}")
            except json.JSONDecodeError:
                logger.warning(f"Invalid config file at {self.config_file}, creating default")
                self.create_default_config()
        else:
            logger.info(f"No config file found at {self.config_file}, creating default")
            self.create_default_config()

    def create_default_config(self):
        """Create default empty configuration"""
        self.config = {"folders": {}}
        self.save_config()

    def save_config(self):
        """Save configuration to file"""
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=2)
        logger.info(f"Saved configuration to {self.config_file}")

    def add_folder(self, folder, repo_url, username, token):
        """Add a folder to be tracked"""
        abs_folder = os.path.abspath(os.path.expanduser(folder))
        
        # Check if folder exists
        if not os.path.isdir(abs_folder):
            logger.error(f"Folder {abs_folder} does not exist")
            return False
        
        # Check if folder is a git repository
        if not os.path.isdir(os.path.join(abs_folder, ".git")):
            logger.error(f"Folder {abs_folder} is not a git repository")
            return False
            
        self.config["folders"][abs_folder] = {
            "repo_url": repo_url,
            "username": username,
            "token": token
        }
        self.save_config()
        logger.info(f"Added folder {abs_folder} to config")
        return True
        
    def remove_folder(self, folder):
        """Remove a folder from tracking"""
        abs_folder = os.path.abspath(os.path.expanduser(folder))
        if abs_folder in self.config["folders"]:
            del self.config["folders"][abs_folder]
            self.save_config()
            logger.info(f"Removed folder {abs_folder} from config")
            return True
        else:
            logger.warning(f"Folder {abs_folder} not found in config")
            return False
            
    def get_folders(self):
        """Get all tracked folders"""
        return self.config["folders"]
        
    def get_folder_config(self, folder):
        """Get configuration for a specific folder"""
        abs_folder = os.path.abspath(os.path.expanduser(folder))
        return self.config["folders"].get(abs_folder)
        
    def is_registered_folder(self, folder):
        """Check if a folder is registered"""
        abs_folder = os.path.abspath(os.path.expanduser(folder))
        return abs_folder in self.config["folders"]