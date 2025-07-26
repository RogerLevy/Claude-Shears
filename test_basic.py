#!/usr/bin/env python3
"""
Basic test of shears functionality without TUI
"""

import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from shears.scanner import ProjectScanner
from shears.utils import format_date, format_count

def main():
    print("=== Shears - Claude Project Manager Test ===\n")
    
    scanner = ProjectScanner()
    projects = scanner.scan_projects()
    
    if not projects:
        print("No projects found in ~/.claude/projects")
        return
    
    print(f"Found {len(projects)} projects:\n")
    
    # Show project menu format
    print("PROJECT MENU:")
    print("-" * 80)
    for i, project in enumerate(projects):
        date_str = format_date(project.creation_date)
        conv_count = format_count(project.conversation_count)
        msg_count = format_count(project.total_messages)
        print(f"{i+1:2}. {date_str}  {project.decoded_path}  ({conv_count} conversations, {msg_count} messages)")
    
    # Show first project's conversations
    if projects:
        project = projects[0]
        print(f"\nCONVERSATION MENU - {project.decoded_path}:")
        print("-" * 80)
        for i, conv in enumerate(project.conversations[:5]):  # Show first 5
            date_str = format_date(conv.creation_date)
            msg_count = format_count(conv.message_count)
            print(f"{i+1:2}. {date_str}  {conv.name[:50]}...  ({msg_count} messages)")
    
    print(f"\nTest completed successfully!")
    print("To launch the full TUI, install textual: pip install textual")
    print("Then run: python -m shears.app")

if __name__ == "__main__":
    main()