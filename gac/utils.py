"""
Git Auto Commit - Utility functions
Contains helper functions for git operations and other shared utilities
"""
import os
import subprocess
import logging

logger = logging.getLogger(__name__)

def run_git_command(command, cwd, username=None, token=None, repo_url=None):
    """Run a git command in the specified directory"""
    try:
        # For push commands that need authentication
        env = os.environ.copy()
        if username and token and repo_url and "push" in command:
            # Extract repo domain and path
            if repo_url.startswith("https://"):
                # Convert https://github.com/user/repo.git to https://username:token@github.com/user/repo.git
                parts = repo_url.split("//")
                if len(parts) > 1:
                    domain_path = parts[1]
                    auth_url = f"https://{username}:{token}@{domain_path}"
                    # Replace the remote URL temporarily
                    subprocess.run(["git", "remote", "set-url", "origin", auth_url], 
                                  cwd=cwd, check=True, capture_output=True)
                    logger.debug(f"Set remote URL with authentication for push")

        # Run the actual git command
        result = subprocess.run(command, cwd=cwd, check=True, capture_output=True, text=True)
        
        # Reset remote URL if we modified it
        if username and token and repo_url and "push" in command:
            subprocess.run(["git", "remote", "set-url", "origin", repo_url], 
                          cwd=cwd, check=True, capture_output=True)
            logger.debug(f"Reset remote URL after push")
            
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        error_msg = e.stderr if hasattr(e, 'stderr') else str(e)
        logger.error(f"Git command failed: {error_msg}")
        return False, error_msg

def has_changes(folder):
    """Check if the git repository has uncommitted changes"""
    success, output = run_git_command(["git", "status", "--porcelain"], cwd=folder)
    if not success:
        return False
    return bool(output.strip())

def git_add(folder):
    """Run git add . in the specified folder"""
    return run_git_command(["git", "add", "."], cwd=folder)

def git_commit(folder, message="Auto-commit by GAC"):
    """Run git commit in the specified folder"""
    return run_git_command(["git", "commit", "-m", message], cwd=folder)

def git_push(folder, username, token, repo_url):
    """Run git push in the specified folder"""
    return run_git_command(["git", "push"], cwd=folder, username=username, token=token, repo_url=repo_url)

def commit_and_push(folder, repo_config, commit_message="Auto-commit by GAC"):
    """Commit and push changes for a folder"""
    logger.info(f"Checking for changes in {folder}")
    
    if not has_changes(folder):
        logger.info(f"No changes detected in {folder}")
        return True, "No changes to commit"
    
    logger.info(f"Changes detected in {folder}, committing")
    
    success, output = git_add(folder)
    if not success:
        return False, f"Failed to add changes: {output}"
    
    success, output = git_commit(folder, commit_message)
    if not success:
        return False, f"Failed to commit changes: {output}"
        
    logger.info(f"Successfully committed changes in {folder}")
    
    username = repo_config["username"]
    token = repo_config["token"]
    repo_url = repo_config["repo_url"]
    
    logger.info(f"Pushing changes to remote for {folder}")
    success, output = git_push(folder, username, token, repo_url)
    if not success:
        return False, f"Failed to push changes: {output}"
        
    logger.info(f"Successfully pushed changes for {folder}")
    return True, "Successfully committed and pushed changes"

def is_git_repo(folder):
    """Check if a folder is a git repository"""
    git_dir = os.path.join(folder, ".git")
    return os.path.isdir(git_dir)

def git_init_and_first_commit(folder, repo_url, username, token, initial_commit_message="Initial commit by GAC"):
    """Initialize a git repo, add all files, make initial commit, add remote, and push."""
    # Initialize git repo
    success, output = run_git_command(["git", "init"], cwd=folder)
    if not success:
        return False, f"Failed to initialize git repo: {output}"
    
    # Add all files
    success, output = git_add(folder)
    if not success:
        return False, f"Failed to add files: {output}"
    
    # Commit
    success, output = git_commit(folder, initial_commit_message)
    if not success:
        return False, f"Failed to commit: {output}"
    
    # Add remote origin
    success, output = run_git_command(["git", "remote", "add", "origin", repo_url], cwd=folder)
    if not success and "remote origin already exists" not in output:
        return False, f"Failed to add remote: {output}"
    
    # Detect current branch (main or master)
    try:
        result = subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=folder, capture_output=True, text=True, check=True)
        branch = result.stdout.strip()
    except Exception as e:
        return False, f"Failed to detect current branch: {e}"
    
    # Push to remote with --set-upstream
    success, output = run_git_command(["git", "push", "--set-upstream", "origin", branch], cwd=folder, username=username, token=token, repo_url=repo_url)
    if not success:
        return False, f"Failed to push initial commit: {output}"
    
    return True, "Initialized git repo and pushed initial commit"

def setup_systemd_user_service():
    """Set up a systemd user service to auto-start the watcher on login."""
    import os
    import subprocess
    service_dir = os.path.expanduser("~/.config/systemd/user")
    service_file = os.path.join(service_dir, "gac-watcher.service")
    gac_bin = os.path.expanduser("~/.local/bin/gac")
    service_content = f"""[Unit]
Description=Git Auto Commit Watcher

[Service]
ExecStart={gac_bin} start
Restart=always

[Install]
WantedBy=default.target
"""
    if not os.path.exists(service_dir):
        os.makedirs(service_dir)
    if not os.path.exists(service_file):
        with open(service_file, "w") as f:
            f.write(service_content)
    # Reload systemd user daemon and enable/start the service
    subprocess.run(["systemctl", "--user", "daemon-reload"])
    subprocess.run(["systemctl", "--user", "enable", "--now", "gac-watcher.service"])