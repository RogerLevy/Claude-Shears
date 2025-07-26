"""
Utility functions for shears
"""

import os
import json
import re
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any


def get_claude_projects_dir() -> Path:
    """Get the Claude projects directory"""
    return Path.home() / ".claude" / "projects"


def decode_project_path(encoded_path: str) -> str:
    """
    Decode the project folder name back to the actual path
    
    Example: "-mnt-c-Users-roger-Desktop-shears" -> "/mnt/c/Users/roger/Desktop/shears"
    """
    if encoded_path.startswith("-"):
        # Remove leading dash and replace remaining dashes with slashes
        decoded = encoded_path[1:].replace("-", "/")
        return f"/{decoded}"
    return encoded_path


def format_date(timestamp: str) -> str:
    """Format ISO timestamp to readable date"""
    try:
        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        return dt.strftime('%Y-%m-%d')
    except Exception:
        return "Unknown"


def format_count(count: int) -> str:
    """Format count with appropriate suffix (k, M)"""
    if count >= 1000000:
        return f"{count/1000000:.1f}M"
    elif count >= 1000:
        return f"{count/1000:.1f}k"
    else:
        return str(count)


def truncate_text(text: str, max_length: int = 60) -> str:
    """Truncate text to max length with ellipsis"""
    if len(text) <= max_length:
        return text
    return text[:max_length-3] + "..."


def extract_first_user_message(jsonl_path: Path) -> str:
    """Extract the first user message from a JSONL file, skipping Caveat messages"""
    try:
        with open(jsonl_path, 'r', encoding='utf-8') as f:
            for line in f:
                if not line.strip():
                    continue
                data = json.loads(line)
                if data.get('type') == 'user' and 'message' in data:
                    message = data['message']
                    if isinstance(message, dict) and 'content' in message:
                        content = message['content']
                        if isinstance(content, str):
                            # Clean up content
                            content = re.sub(r'<[^>]+>', '', content)  # Remove HTML-like tags
                            content = content.strip()
                            if content and not content.startswith('Caveat:'):
                                return truncate_text(content)
                        elif isinstance(content, list):
                            # Handle content as list of objects
                            for item in content:
                                if isinstance(item, dict) and item.get('type') == 'text':
                                    text = item.get('text', '').strip()
                                    if text and not text.startswith('Caveat:'):
                                        text = re.sub(r'<[^>]+>', '', text)
                                        if text:
                                            return truncate_text(text)
                    # If this user message started with Caveat:, continue to next message
        return "Empty conversation"
    except Exception:
        return "Unable to read conversation"