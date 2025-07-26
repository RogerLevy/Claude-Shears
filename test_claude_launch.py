#!/usr/bin/env python3
"""
Test Claude launch functionality
"""

import sys
import os
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from shears.scanner import ProjectScanner

def test_claude_launch():
    """Test that we can construct a valid Claude launch command"""
    print("=== Testing Claude Launch Logic ===\n")
    
    scanner = ProjectScanner()
    projects = scanner.scan_projects()
    
    if not projects:
        print("No projects found")
        return
    
    # Get first project with conversations
    for project in projects:
        if project.conversations:
            conversation = project.conversations[0]
            
            print(f"Testing launch for conversation: {conversation.name[:50]}...")
            print(f"Project path: {project.decoded_path}")
            print(f"Session ID: {conversation.session_id}")
            
            # Test command construction
            cmd = ["claude", "--resume", conversation.session_id]
            print(f"Command would be: {' '.join(cmd)}")
            print(f"Working directory would be: {project.decoded_path}")
            
            # Test if working directory exists
            if os.path.exists(project.decoded_path):
                print("✓ Working directory exists")
            else:
                print("✗ Working directory does not exist")
            
            # Test if claude command exists
            try:
                import subprocess
                result = subprocess.run(["which", "claude"], capture_output=True, text=True)
                if result.returncode == 0:
                    print(f"✓ Claude command found at: {result.stdout.strip()}")
                else:
                    print("✗ Claude command not found")
                    
                # Test the actual command that would be executed
                print(f"\nFull command would be:")
                print(f"  subprocess.run({cmd}, cwd='{project.decoded_path}')")
                
            except Exception as e:
                print(f"✗ Error checking claude command: {e}")
            
            print("\nLaunch test completed successfully!")
            return
    
    print("No conversations found to test")

if __name__ == "__main__":
    test_claude_launch()