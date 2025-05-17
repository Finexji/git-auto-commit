"""
Git Auto Commit - A tool to automatically commit local folders to GitHub
"""
import logging

# Setup basic logging configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

# Package metadata
__version__ = "1.0.0"
__author__ = "Finex - revoke"
__description__ = "Automatically commit local folders to GitHub"

# Import main modules
from .cli import main
from .gui import launch_gui
from .watcher import Watcher
from .config import Config