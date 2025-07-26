# Shears - Claude Project Manager

An interactive console tool for managing Claude Code projects and conversations.

## Features

- **Project Menu**: Browse all Claude projects sorted by creation date
- **Conversation Menu**: View conversations within each project
- **Conversation Management**: Rename, delete, and launch conversations
- **Smart Naming**: Uses conversation summaries or first message excerpts
- **Metadata Storage**: Tracks custom names and conversation info in `shears.json` files
- **Direct Integration**: Launches Claude Code with `--resume` functionality

## Installation & Usage

### Global Installation (Ready to Use!)
The shears executable is already installed at `/home/roger/bin/shears` and ready to use with no additional dependencies:

```bash
# Run from anywhere - no setup needed!
shears
```

### Quick Test (No Dependencies)
```bash
cd /mnt/c/Users/roger/Desktop/shears
python3 test_basic.py
```

### Alternative Methods
```bash
# Run from project directory
cd /mnt/c/Users/roger/Desktop/shears
python3 run_shears.py

# Install as Python package
pip install -e .
shears
```

## Navigation

### Project Menu
- **Arrow Keys**: Navigate projects
- **Enter**: Select project
- **Ctrl+C**: Quit

### Conversation Menu
- **Arrow Keys**: Navigate conversations
- **Enter**: Launch Claude Code with selected conversation
- **R**: Rename conversation
- **Delete**: Delete conversation (with confirmation)
- **Escape**: Back to project menu
- **Ctrl+C**: Quit

## How It Works

1. **Project Detection**: Scans `~/.claude/projects/` for project folders
2. **Path Decoding**: Converts encoded folder names back to readable paths
3. **Metadata Creation**: Analyzes JSONL files to extract conversation info
4. **Smart Naming**: 
   - Uses summary title if available (unless contains "Caveat")
   - Falls back to first user message excerpt
   - Stores custom names in `shears.json` files
5. **Claude Integration**: Launches `claude --resume <session-id>` in correct directory

## Project Structure

```
shears/
├── shears/
│   ├── __init__.py
│   ├── app.py           # Main TUI application
│   ├── scanner.py       # Project/conversation discovery
│   ├── metadata.py      # shears.json management
│   └── utils.py         # Helper functions
├── setup.py
├── run_shears.py        # Standalone launcher
├── test_basic.py        # Test without TUI
└── README.md
```

## Display Format

### Project Menu
```
2025-07-26  ~/Desktop/vfxland5  (150 conversations, 2.3k messages)
2025-07-25  ~/Desktop/shears    (1 conversations, 70 messages)
```

### Conversation Menu
```
2025-07-26  VFX Forth Hanoi Implementation  (47 messages)
2025-07-25  Project setup and configuration  (23 messages)
```

## Requirements

- Python 3.8+
- textual >= 0.41.0 (for TUI interface)
- rich >= 13.0.0 (for text formatting)
- Claude Code CLI installed and accessible

## Notes

- Metadata files (`*.shears.json`) are created alongside each JSONL file
- Projects are sorted by earliest conversation creation date (descending)
- Conversations are sorted by creation date (descending)
- Supports both current directory detection and global project browsing