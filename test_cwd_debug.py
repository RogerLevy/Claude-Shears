#!/usr/bin/env python3
"""
Debug working directory behavior in subprocess
"""

import os
import subprocess
import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from shears.scanner import ProjectScanner

def test_subprocess_cwd():
    """Test subprocess working directory behavior"""
    print("=== Testing Subprocess CWD Behavior ===\n")
    
    scanner = ProjectScanner()
    projects = scanner.scan_projects()
    
    if not projects:
        print("No projects found")
        return
    
    # Find the project from vfxland5_starling directory
    target_project = None
    for project in projects:
        if "vfxland5_starling" in project.decoded_path or "vfxland5/starling" in project.decoded_path:
            target_project = project
            break
    
    if not target_project and projects:
        # Fall back to first project
        target_project = projects[0]
    
    if not target_project:
        print("No suitable project found")
        return
    
    print(f"Testing with project: {target_project.decoded_path}")
    
    if target_project.conversations:
        conversation = target_project.conversations[0]
        print(f"Testing with conversation: {conversation.name[:50]}...")
        print(f"Session ID: {conversation.session_id}")
        
        # Test 1: Current working directory
        print(f"\nCurrent working directory: {os.getcwd()}")
        
        # Test 2: Target directory exists check
        target_dir = target_project.decoded_path
        print(f"Target directory: {target_dir}")
        print(f"Target directory exists: {os.path.exists(target_dir)}")
        
        # Test 3: Test subprocess with cwd parameter
        test_cmd = ["pwd"]
        print(f"\nTesting subprocess.run with cwd parameter:")
        print(f"Command: {test_cmd}")
        print(f"CWD parameter: {target_dir}")
        
        try:
            result = subprocess.run(test_cmd, cwd=target_dir, capture_output=True, text=True)
            print(f"Return code: {result.returncode}")
            print(f"Stdout: {result.stdout.strip()}")
            print(f"Stderr: {result.stderr.strip()}")
        except Exception as e:
            print(f"Error: {e}")
        
        # Test 4: Test with actual Claude command (dry run)
        claude_cmd = ["claude", "--version"]
        print(f"\nTesting Claude command availability:")
        try:
            result = subprocess.run(claude_cmd, cwd=target_dir, capture_output=True, text=True)
            print(f"Claude version check return code: {result.returncode}")
            print(f"Claude version: {result.stdout.strip()}")
        except Exception as e:
            print(f"Claude command error: {e}")
        
        # Test 5: Show what the actual resume command would be
        resume_cmd = ["claude", "--resume", conversation.session_id]
        print(f"\nActual resume command would be:")
        print(f"  subprocess.run({resume_cmd}, cwd='{target_dir}')")
        
        print(f"\nTo manually test, run:")
        print(f"  cd '{target_dir}'")
        print(f"  claude --resume {conversation.session_id}")

if __name__ == "__main__":
    test_subprocess_cwd()