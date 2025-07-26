#!/usr/bin/env python3
"""
Debug the actual message structure in JSONL files
"""

import json
import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from shears.scanner import ProjectScanner

def debug_message_structure():
    """Debug actual message structure in JSONL files"""
    print("=== Debugging Message Structure ===\n")
    
    scanner = ProjectScanner()
    projects = scanner.scan_projects()
    
    if not projects:
        print("No projects found")
        return
    
    # Find a project with conversations
    for project in projects:
        if project.conversations:
            conversation = project.conversations[0]
            print(f"Examining: {conversation.name}")
            print(f"File: {conversation.jsonl_path}")
            print()
            
            try:
                with open(conversation.jsonl_path, 'r', encoding='utf-8') as f:
                    for line_num, line in enumerate(f, 1):
                        if line_num > 5:  # Only check first 5 lines
                            break
                        
                        if not line.strip():
                            continue
                        
                        try:
                            data = json.loads(line)
                            message_type = data.get('type', 'unknown')
                            
                            print(f"=== Line {line_num}: {message_type} ===")
                            
                            if message_type in ['user', 'assistant']:
                                message = data.get('message', {})
                                print(f"Message keys: {list(message.keys())}")
                                
                                if 'content' in message:
                                    content = message['content']
                                    print(f"Content type: {type(content)}")
                                    
                                    if isinstance(content, list):
                                        print(f"Content list length: {len(content)}")
                                        for i, item in enumerate(content):
                                            print(f"  Item {i}: {type(item)} - {list(item.keys()) if isinstance(item, dict) else item}")
                                            if isinstance(item, dict) and 'text' in item:
                                                text = item['text']
                                                print(f"    Text preview: {repr(text[:100])}")
                                    else:
                                        print(f"Content: {repr(content[:100] if isinstance(content, str) else content)}")
                                
                                print()
                            
                        except json.JSONDecodeError as e:
                            print(f"JSON error on line {line_num}: {e}")
                
            except Exception as e:
                print(f"Error reading file: {e}")
            
            break  # Only examine first conversation
    
    print("Debug complete!")

if __name__ == "__main__":
    debug_message_structure()