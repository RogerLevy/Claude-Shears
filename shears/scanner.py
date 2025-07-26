"""
Project and conversation scanning functionality
"""

import os
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from .utils import get_claude_projects_dir, decode_project_path, format_date, format_count
from .metadata import ConversationMetadata


@dataclass
class ProjectInfo:
    """Information about a Claude project"""
    encoded_path: str
    decoded_path: str  # Display name (custom name or decoded path)
    working_path: str  # Actual working directory path
    creation_date: str
    conversation_count: int
    total_messages: int
    conversations: List['ConversationInfo'] = None
    
    def __post_init__(self):
        if self.conversations is None:
            self.conversations = []


@dataclass 
class ConversationInfo:
    """Information about a conversation"""
    session_id: str
    name: str
    creation_date: str
    message_count: int
    jsonl_path: Path
    metadata: ConversationMetadata


class ProjectScanner:
    """Scans Claude projects directory and manages project/conversation data"""
    
    def __init__(self):
        self.projects_dir = get_claude_projects_dir()
        self._projects = None
    
    def scan_projects(self) -> List[ProjectInfo]:
        """Scan all projects and return sorted list"""
        if not self.projects_dir.exists():
            return []
        
        projects = []
        
        for project_dir in self.projects_dir.iterdir():
            if not project_dir.is_dir():
                continue
                
            project_info = self._scan_project(project_dir)
            if project_info:
                projects.append(project_info)
        
        # Sort by creation date descending
        projects.sort(key=lambda p: p.creation_date, reverse=True)
        
        self._projects = projects
        return projects
    
    def _scan_project(self, project_dir: Path) -> Optional[ProjectInfo]:
        """Scan a single project directory"""
        jsonl_files = list(project_dir.glob("*.jsonl"))
        if not jsonl_files:
            return None
        
        conversations = []
        total_messages = 0
        earliest_date = None
        
        for jsonl_file in jsonl_files:
            try:
                metadata = ConversationMetadata(jsonl_file)
                conv_info = ConversationInfo(
                    session_id=metadata.session_id,
                    name=metadata.name,
                    creation_date=metadata.creation_date,
                    message_count=metadata.message_count,
                    jsonl_path=jsonl_file,
                    metadata=metadata
                )
                conversations.append(conv_info)
                total_messages += metadata.message_count
                
                # Track earliest creation date
                if earliest_date is None or metadata.creation_date < earliest_date:
                    earliest_date = metadata.creation_date
                    
            except Exception:
                continue
        
        if not conversations:
            return None
        
        # Sort conversations by creation date descending
        conversations.sort(key=lambda c: c.creation_date, reverse=True)
        
        # Check for custom project name and corrected path
        project_metadata = self._load_project_metadata(project_dir)
        display_path = project_metadata.get("custom_name", decode_project_path(project_dir.name))
        
        # Use corrected path if available, otherwise use decoded path
        actual_path = project_metadata.get("corrected_path", decode_project_path(project_dir.name))
        
        return ProjectInfo(
            encoded_path=project_dir.name,
            decoded_path=display_path,
            working_path=actual_path,
            creation_date=earliest_date or "2000-01-01T00:00:00.000Z",
            conversation_count=len(conversations),
            total_messages=total_messages,
            conversations=conversations
        )
    
    def get_project_by_path(self, current_path: str) -> Optional[ProjectInfo]:
        """Find project that matches the current working directory"""
        if self._projects is None:
            self.scan_projects()
        
        # Normalize paths for comparison
        current_path = os.path.normpath(current_path)
        
        # First try exact match with working_path
        for project in self._projects:
            project_path = os.path.normpath(project.working_path)
            if current_path == project_path:
                return project
        
        # If no exact match, try to find if current path might be a related project directory
        # This handles cases where the decoded path is incorrect due to underscores vs slashes
        for project in self._projects:
            # Check if the current path contains key parts of the encoded path
            encoded_parts = project.encoded_path.replace('-', '_').split('_')
            # Remove empty parts and common prefixes
            significant_parts = [part for part in encoded_parts if part and part not in ['mnt', 'c', 'Users']]
            
            # If current path contains the significant parts, it might be the right project
            if len(significant_parts) > 2:  # Only check if we have enough unique parts
                path_lower = current_path.lower()
                if all(part.lower() in path_lower for part in significant_parts[-3:]):  # Check last 3 parts
                    return project
        
        return None
    
    def refresh_project(self, project: ProjectInfo) -> ProjectInfo:
        """Refresh a specific project's conversation data"""
        project_dir = self.projects_dir / project.encoded_path
        return self._scan_project(project_dir)
    
    def delete_conversation(self, conversation: ConversationInfo) -> bool:
        """Delete a conversation and its metadata"""
        try:
            # Delete JSONL file
            if conversation.jsonl_path.exists():
                conversation.jsonl_path.unlink()
            
            # Delete metadata file
            metadata_path = conversation.metadata.metadata_path
            if metadata_path.exists():
                metadata_path.unlink()
            
            return True
        except Exception:
            return False
    
    def get_current_working_directory_project(self) -> Optional[ProjectInfo]:
        """Check if current working directory corresponds to a Claude project"""
        try:
            cwd = os.getcwd()
            return self.get_project_by_path(cwd)
        except Exception:
            return None
    
    def rename_project(self, project: ProjectInfo, new_name: str) -> bool:
        """Rename a project by updating its metadata"""
        try:
            # Create/update project metadata file
            project_dir = self.projects_dir / project.encoded_path
            metadata_path = project_dir / ".shears_project.json"
            
            # Load existing metadata or create new
            existing_metadata = self._load_project_metadata(project_dir)
            existing_metadata.update({
                "custom_name": new_name,
                "original_path": project.decoded_path
            })
            
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(existing_metadata, f, indent=2)
            
            return True
        except Exception:
            return False
    
    def set_project_path(self, project: ProjectInfo, corrected_path: str) -> bool:
        """Set the corrected path for a project"""
        try:
            # Create/update project metadata file
            project_dir = self.projects_dir / project.encoded_path
            metadata_path = project_dir / ".shears_project.json"
            
            # Load existing metadata or create new
            existing_metadata = self._load_project_metadata(project_dir)
            existing_metadata.update({
                "corrected_path": corrected_path,
                "original_path": project.decoded_path
            })
            
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(existing_metadata, f, indent=2)
            
            return True
        except Exception:
            return False
    
    def _load_project_metadata(self, project_dir: Path) -> Dict[str, str]:
        """Load project metadata from .shears_project.json"""
        metadata_path = project_dir / ".shears_project.json"
        if metadata_path.exists():
            try:
                with open(metadata_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                pass
        return {}