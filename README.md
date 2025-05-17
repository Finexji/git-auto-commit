# Git Auto Commit (GAC)

Automatically commit and push changes in your local folders to GitHub, with a modern dark-themed GUI and robust background watcher.

## Features
- **Modern dark mode GUI** (with light mode toggle)
- **Auto-commit and push** for registered folders
- **Systemd user service** for background watching (auto-starts on login)
- **Easy folder registration and removal** (via GUI or CLI)
- **No manual dependency management needed**

## Installation

### With pipx (Recommended)
```bash
pipx install .
```
- All dependencies (including `ttkbootstrap` for the GUI) are installed automatically.
- No need to run `pipx inject` manually.

### With pip
```bash
pip install .
```

## Usage

### Launch the GUI
```bash
gac gui
```
- Register folders, edit/remove them, and toggle dark/light mode from the GUI.
- Right-click a folder in the "Manage Folders" tab to remove or edit it.

### CLI Commands
- Add a folder:
  ```bash
  gac add <folder> <repo_url> <username> <token>
  ```
- List folders:
  ```bash
  gac list
  ```
- Commit current folder:
  ```bash
  gac commit
  ```

### Systemd Watcher Service
- The watcher service is set up automatically when you register your first folder.
- It runs in the background and auto-starts on login.
- To check status:
  ```bash
  systemctl --user status gac-watcher.service
  ```
- To restart:
  ```bash
  systemctl --user restart gac-watcher.service
  ```

#### Troubleshooting
- If the watcher fails to start, check logs:
  ```bash
  journalctl --user -u gac-watcher.service -e
  ```
- If you update the code, **reinstall with**:
  ```bash
  pipx install . --force
  # or
  pipx reinstall gac
  ```
- Then reload and restart the service:
  ```bash
  systemctl --user daemon-reload
  systemctl --user restart gac-watcher.service
  ```

## Notes
- No need to run `pipx inject` for dependencies—everything is handled automatically.
- The GUI is fully modern, dark-themed by default, and easy to use.
- Removing a folder is as simple as right-clicking it in the GUI or using the CLI.

---

Enjoy seamless, automatic Git commits and pushes with a beautiful, modern interface!

## Development

### Project Structure

```
gac/
├── gac/
│   ├── __init__.py
│   ├── cli.py
│   ├── gui.py
│   ├── watcher.py
│   ├── config.py
│   └── utils.py
├── setup.py
├── requirements.txt
└── README.md
```

### Requirements

- watchdog: For file system monitoring
- tkinter: For the GUI interface (usually comes with Python)
- pipx: For global CLI installation (recommended)

## License

MIT License

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.