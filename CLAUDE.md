# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Shears is an interactive TUI (Terminal User Interface) tool for managing Claude Code projects and conversations. It provides a console-based interface to browse, rename, delete, view, and launch Claude conversations across all projects.

## Core Commands

### Testing
```bash
# Quick test without TUI dependencies
python3 test_basic.py

# Test with full TUI
python3 run_shears.py
# or
shears
```

### Installation & Running
```bash
# Install dependencies (multiple fallback methods)
./install_deps.sh

# Run standalone (no installation)
python3 run_shears.py

# Install as package and run
pip install -e .
shears
```

### Development Commands
```bash
# Install dependencies manually
pip install textual>=0.41.0 rich>=13.0.0

# Run from module
python -m shears.app
```

## Architecture

### Core Components

- **`shears/app.py`**: Main TUI application using Textual framework
  - `ShearsApp`: Main application class with project and conversation screens
  - `ConfirmDialog`: Modal for delete confirmations
  - `RenameDialog`: Modal for renaming conversations and projects
  - `PathCorrectionDialog`: Modal for correcting invalid project paths
  - `ConversationViewer`: Full-screen conversation content viewer with scrolling
  - `ConversationListView`: Custom ListView with conversation management
  - `ProjectListView`: Custom ListView with project management

- **`shears/scanner.py`**: Project and conversation discovery
  - `ProjectScanner`: Scans `~/.claude/projects/` for Claude projects
  - `ProjectInfo`: Data class for project metadata with path correction support
  - `ConversationInfo`: Data class for conversation metadata
  - Project metadata management with `.shears_project.json` files

- **`shears/metadata.py`**: Metadata file management
  - `ConversationMetadata`: Manages `.shears.json` files alongside JSONL files
  - Handles custom names and conversation properties
  - Auto-regeneration of metadata to filter out "Caveat:" messages

- **`shears/utils.py`**: Core utilities
  - `decode_project_path()`: Converts encoded folder names to readable paths
  - `extract_first_user_message()`: Parses JSONL to extract conversation previews
  - Enhanced content extraction supporting text, tool_use, and tool_result formats
  - Date/count formatting helpers

### Data Flow

1. **Project Discovery**: Scanner reads `~/.claude/projects/` directory
2. **Path Decoding**: Converts encoded folder names (e.g., `-mnt-c-Users-...`) to readable paths
3. **Path Validation**: Checks if decoded paths exist; prompts for correction if not
4. **Conversation Analysis**: Parses JSONL files to extract metadata and message counts
5. **Content Filtering**: Automatically filters out "Caveat:" messages from conversation names
6. **Metadata Management**: Creates/updates `.shears.json` and `.shears_project.json` files
7. **Claude Integration**: Launches `claude --resume <session-id>` in correct directory

### File Structure Patterns

- JSONL files contain conversation data in Claude's format with text, tool_use, and tool_result content
- `.shears.json` files store conversation metadata (custom names, properties)
- `.shears_project.json` files store project metadata (corrected paths, custom names)
- Projects sorted by earliest conversation date (descending)
- Conversations sorted by creation date (descending)

## Key Dependencies

- **textual**: TUI framework for the interactive interface
- **rich**: Text formatting and styling
- Standard library only for core functionality

## Integration Points

- Reads Claude's project structure from `~/.claude/projects/`
- Launches Claude Code using `claude --resume <session-id>`
- Changes working directory to project path before launching Claude
- Handles path correction for moved or renamed project directories
- Supports current working directory detection for seamless project switching

## User Interface Features

### Navigation
- **Page Up/Down**: Navigate through projects and conversations by page
- **Arrow Keys**: Move selection up/down
- **Enter**: Select/launch item
- **Escape**: Go back to previous screen
- **Ctrl+C**: Quit application

### Project Management
- **R Key**: Rename project (stores custom name in metadata)
- **Enter**: View conversations in project
- Auto-detection of current working directory project

### Conversation Management
- **V Key**: View conversation content with full scrolling support
- **R Key**: Rename conversation (stores custom name in metadata)
- **Delete Key**: Delete conversation (with confirmation)
- **Enter**: Launch Claude with conversation

### Content Viewing
- High-performance scrollable conversation viewer
- Supports all Claude message types: text, tool_use, tool_result
- Proper formatting with timestamps and role indicators
- Individual message elements for smooth scrolling performance

### Error Handling
- Path correction dialog for invalid project paths
- Graceful handling of malformed JSONL files
- Automatic metadata regeneration and cleanup