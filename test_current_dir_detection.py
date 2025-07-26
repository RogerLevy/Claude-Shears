#!/usr/bin/env python3
"""
Debug current directory project detection
"""

import os
import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from shears.scanner import ProjectScanner

def test_current_dir_detection():
    """Test current directory project detection"""
    print("=== Testing Current Directory Project Detection ===\n")
    
    scanner = ProjectScanner()
    projects = scanner.scan_projects()
    
    print(f"Current working directory: {os.getcwd()}")
    print(f"Found {len(projects)} total projects:\n")
    
    for i, project in enumerate(projects, 1):
        print(f"{i}. Encoded: {project.encoded_path}")
        print(f"   Display: {project.decoded_path}")
        print(f"   Working: {project.working_path}")
        print(f"   Working path exists: {os.path.exists(project.working_path)}")
        print()
    
    # Test current directory detection
    print("Testing get_current_working_directory_project():")
    current_project = scanner.get_current_working_directory_project()
    
    if current_project:
        print(f"✓ Found current project: {current_project.decoded_path}")
        print(f"  Working path: {current_project.working_path}")
    else:
        print("✗ No current project detected")
    
    # Test with simulated vfxland5_starling directory
    test_path = "/mnt/c/Users/roger/Desktop/vfxland5_starling"
    print(f"\nTesting with simulated path: {test_path}")
    simulated_project = scanner.get_project_by_path(test_path)
    
    if simulated_project:
        print(f"✓ Found project for simulated path: {simulated_project.decoded_path}")
        print(f"  Working path: {simulated_project.working_path}")
    else:
        print("✗ No project found for simulated path")
        
        # Manual check - see which paths might match
        print(f"\nManual path matching for: {test_path}")
        for project in projects:
            norm_project = os.path.normpath(project.working_path)
            norm_test = os.path.normpath(test_path)
            print(f"  Project: {norm_project}")
            print(f"  Test:    {norm_test}")
            print(f"  Match:   {norm_test == norm_project}")
            
            # Test the fuzzy matching logic
            encoded_parts = project.encoded_path.replace('-', '_').split('_')
            significant_parts = [part for part in encoded_parts if part and part not in ['mnt', 'c', 'Users']]
            print(f"  Encoded: {project.encoded_path}")
            print(f"  Parts:   {significant_parts}")
            if len(significant_parts) > 2:
                last_parts = significant_parts[-3:]
                path_lower = test_path.lower()
                matches = [part.lower() in path_lower for part in last_parts]
                print(f"  Last 3:  {last_parts}")
                print(f"  Matches: {matches} -> {all(matches)}")
            print()

if __name__ == "__main__":
    test_current_dir_detection()