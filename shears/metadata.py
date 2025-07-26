"""
Metadata management for shears.json files
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional
from .utils import extract_first_user_message


class ConversationMetadata:
    """Manages metadata for a single conversation"""
    
    def __init__(self, jsonl_path: Path):
        self.jsonl_path = jsonl_path
        self.metadata_path = jsonl_path.with_name(f"{jsonl_path.stem}.shears.json")
        self._metadata = self._load_metadata()
    
    def _load_metadata(self) -> Dict[str, Any]:
        """Load metadata from shears.json file, creating if needed"""
        if self.metadata_path.exists():
            try:
                with open(self.metadata_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                pass
        
        # Create new metadata
        return self._create_initial_metadata()
    
    def _create_initial_metadata(self) -> Dict[str, Any]:
        """Create initial metadata by analyzing the JSONL file"""
        name = self._determine_conversation_name()
        creation_date = self._get_creation_date()
        message_count = self._count_messages()
        
        metadata = {
            "name": name,
            "custom_name": None,
            "creation_date": creation_date,
            "message_count": message_count,
            "last_updated": creation_date
        }
        
        self._save_metadata(metadata)
        return metadata
    
    def _determine_conversation_name(self) -> str:
        """Determine conversation name based on summary or first message"""
        try:
            with open(self.jsonl_path, 'r', encoding='utf-8') as f:
                # Check first line for summary
                first_line = f.readline().strip()
                if first_line:
                    data = json.loads(first_line)
                    if data.get('type') == 'summary' and 'summary' in data:
                        summary = data['summary']
                        # Use summary unless it contains "Caveat"
                        if 'Caveat' not in summary:
                            return summary
                
                # Fall back to first user message
                return extract_first_user_message(self.jsonl_path)
        except Exception:
            return f"Conversation {self.jsonl_path.stem[:8]}"
    
    def _get_creation_date(self) -> str:
        """Get creation date from first message timestamp"""
        try:
            with open(self.jsonl_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if not line.strip():
                        continue
                    data = json.loads(line)
                    if 'timestamp' in data:
                        return data['timestamp']
        except Exception:
            pass
        
        # Fall back to file modification time
        try:
            mtime = self.jsonl_path.stat().st_mtime
            from datetime import datetime
            return datetime.fromtimestamp(mtime).isoformat() + 'Z'
        except Exception:
            return "2000-01-01T00:00:00.000Z"
    
    def _count_messages(self) -> int:
        """Count total messages in conversation"""
        count = 0
        try:
            with open(self.jsonl_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        data = json.loads(line)
                        if data.get('type') in ['user', 'assistant']:
                            count += 1
        except Exception:
            pass
        return count
    
    def _save_metadata(self, metadata: Dict[str, Any]) -> None:
        """Save metadata to shears.json file"""
        try:
            with open(self.metadata_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2)
            with open("/tmp/shears_debug.log", "a") as f:
                f.write(f"DEBUG: Successfully saved metadata to {self.metadata_path}\n")
                f.write(f"DEBUG: custom_name in saved metadata: {metadata.get('custom_name')}\n")
        except Exception as e:
            with open("/tmp/shears_debug.log", "a") as f:
                f.write(f"DEBUG: ERROR saving metadata to {self.metadata_path}: {e}\n")
    
    @property
    def name(self) -> str:
        """Get conversation name (custom name if set, otherwise default)"""
        custom_name = self._metadata.get('custom_name')
        if custom_name:
            return custom_name
        
        default_name = self._metadata.get('name', 'Unknown')
        # If the stored name starts with Caveat:, regenerate it
        if default_name.startswith('Caveat:'):
            default_name = self._determine_conversation_name()
            self._metadata['name'] = default_name
            self._save_metadata(self._metadata)
        
        return default_name
    
    @property
    def creation_date(self) -> str:
        """Get creation date"""
        return self._metadata.get('creation_date', '2000-01-01T00:00:00.000Z')
    
    @property
    def message_count(self) -> int:
        """Get message count"""
        return self._metadata.get('message_count', 0)
    
    @property
    def session_id(self) -> str:
        """Get session ID from filename"""
        return self.jsonl_path.stem
    
    def set_custom_name(self, name: str) -> None:
        """Set custom conversation name"""
        with open("/tmp/shears_debug.log", "a") as f:
            f.write(f"DEBUG: set_custom_name called with name='{name}'\n")
            f.write(f"DEBUG: metadata_path={self.metadata_path}\n")
            f.write(f"DEBUG: metadata_path exists: {self.metadata_path.exists()}\n")
        
        self._metadata['custom_name'] = name
        
        with open("/tmp/shears_debug.log", "a") as f:
            f.write(f"DEBUG: Set custom_name in metadata dict to '{name}'\n")
            f.write(f"DEBUG: About to call _save_metadata\n")
        
        self._save_metadata(self._metadata)
    
    def refresh(self) -> None:
        """Refresh metadata by re-analyzing the JSONL file"""
        self._metadata['message_count'] = self._count_messages()
        self._save_metadata(self._metadata)