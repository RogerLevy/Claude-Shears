"""
Main Shears TUI application
"""

import os
import sys
import subprocess
from pathlib import Path
from typing import List, Optional

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Header, Footer, ListView, ListItem, Label, Input
from textual.binding import Binding
from textual.screen import Screen, ModalScreen
from textual import events
from rich.text import Text

from .scanner import ProjectScanner, ProjectInfo, ConversationInfo
from .utils import format_date, format_count


class ConfirmDialog(ModalScreen):
    """Modal dialog for confirmation"""
    
    def __init__(self, title: str, message: str):
        super().__init__()
        self.title = title
        self.message = message
        self.result = False
    
    def compose(self) -> ComposeResult:
        yield Container(
            Label(self.title, classes="dialog-title"),
            Label(self.message, classes="dialog-message"),
            Horizontal(
                Label("Press Y to confirm, N to cancel", classes="dialog-help"),
                classes="dialog-buttons"
            ),
            classes="dialog"
        )
    
    def key_y(self) -> None:
        self.result = True
        self.dismiss()
    
    def key_n(self) -> None:
        self.result = False
        self.dismiss()
    
    def key_escape(self) -> None:
        self.result = False
        self.dismiss()


class RenameDialog(ModalScreen):
    """Modal dialog for renaming conversations"""
    
    def __init__(self, current_name: str):
        super().__init__()
        self.current_name = current_name
        self.new_name = None
    
    def compose(self) -> ComposeResult:
        yield Container(
            Label("Rename Conversation", classes="dialog-title"),
            Input(value=self.current_name, placeholder="Enter new name", id="name_input"),
            Label("Press Enter to confirm, Escape to cancel", classes="dialog-help"),
            classes="dialog"
        )
    
    def on_mount(self) -> None:
        self.query_one("#name_input", Input).focus()
    
    def on_input_submitted(self, event: Input.Submitted) -> None:
        self.new_name = event.value.strip()
        if self.new_name:
            self.dismiss()
    
    def key_escape(self) -> None:
        self.new_name = None
        self.dismiss()


class PathCorrectionDialog(ModalScreen):
    """Modal dialog for correcting project paths"""
    
    def __init__(self, current_path: str, project_name: str):
        super().__init__()
        self.current_path = current_path
        self.project_name = project_name
        self.corrected_path = None
    
    def compose(self) -> ComposeResult:
        yield Container(
            Label("Correct Project Path", classes="dialog-title"),
            Label(f"Project: {self.project_name}", classes="dialog-message"),
            Label(f"Current path not found: {self.current_path}", classes="dialog-message"),
            Input(value=self.current_path, placeholder="Enter correct path", id="path_input"),
            Label("Press Enter to confirm, Escape to cancel", classes="dialog-help"),
            classes="dialog"
        )
    
    def on_mount(self) -> None:
        self.query_one("#path_input", Input).focus()
    
    def on_input_submitted(self, event: Input.Submitted) -> None:
        self.corrected_path = event.value.strip()
        if self.corrected_path:
            self.dismiss()
    
    def key_enter(self) -> None:
        """Handle Enter key press"""
        input_widget = self.query_one("#path_input", Input)
        self.corrected_path = input_widget.value.strip()
        if self.corrected_path:
            self.dismiss()
    
    def key_escape(self) -> None:
        self.corrected_path = None
        self.dismiss()


class ConversationViewer(Screen):
    """Screen for viewing conversation content with scrolling"""
    
    CSS = """
    .user-header {
        color: $primary;
        text-style: bold;
    }
    
    .assistant-header {
        color: $secondary;
        text-style: bold;
    }
    
    .summary-message {
        color: $warning;
        text-style: bold;
    }
    
    .user-content {
        margin: 0 2;
    }
    
    .assistant-content {
        margin: 0 2;
    }
    
    .no-content {
        color: $text-muted;
        margin: 0 2;
    }
    
    .error-message {
        color: $error;
    }
    
    .message-spacer {
        height: 1;
    }
    
    #conversation_scroll {
        height: 1fr;
        scrollbar-size-vertical: 3;
    }
    
    #conversation_content {
        height: auto;
    }
    """
    
    BINDINGS = [
        Binding("r", "rename", "Rename"),
        Binding("delete", "delete", "Delete"),
        Binding("escape", "back", "Back"),
        Binding("ctrl+c", "quit", "Quit"),
        Binding("pageup", "page_up", "Page Up"),
        Binding("pagedown", "page_down", "Page Down"),
        Binding("enter", "launch", "Launch"),
    ]
    
    def __init__(self, conversation: ConversationInfo):
        super().__init__()
        self.conversation = conversation
    
    def compose(self) -> ComposeResult:
        from textual.widgets import Static
        from textual.containers import ScrollableContainer, Vertical
        
        title = f"Viewing: {self.conversation.name}"
        hotkeys = "R=Rename  Del=Delete  Enter=Launch  Esc=Back  PgUp/PgDn=Scroll  Ctrl+C=Quit"
        
        # Create message elements
        message_elements = self._create_message_elements()
        
        yield Header(show_clock=False)
        yield Label(title, classes="screen-title")
        yield ScrollableContainer(
            Vertical(*message_elements, id="conversation_content"),
            id="conversation_scroll"
        )
        yield Label(hotkeys, classes="hotkeys")
    
    def _create_message_elements(self):
        """Create individual message elements for better scrolling performance"""
        from textual.widgets import Static
        
        elements = []
        
        try:
            import json
            
            with open(self.conversation.jsonl_path, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    if not line.strip():
                        continue
                    
                    try:
                        data = json.loads(line)
                        message_type = data.get('type', 'unknown')
                        
                        if message_type == 'summary':
                            summary_text = f"📋 SUMMARY: {data.get('summary', 'No summary')}"
                            elements.append(Static(summary_text, classes="summary-message"))
                            elements.append(Static("-" * 80, classes="separator"))
                        
                        elif message_type == 'user':
                            timestamp = data.get('timestamp', 'Unknown time')
                            header = f"👤 USER [{timestamp[:19]}]:"
                            elements.append(Static(header, classes="user-header"))
                            
                            message = data.get('message', {})
                            content = self._extract_message_content(message)
                            if content.strip():
                                elements.append(Static(content, classes="user-content"))
                            else:
                                elements.append(Static("[No content or unable to extract]", classes="no-content"))
                            
                            # Add spacing
                            elements.append(Static("", classes="message-spacer"))
                        
                        elif message_type == 'assistant':
                            timestamp = data.get('timestamp', 'Unknown time')
                            header = f"🤖 ASSISTANT [{timestamp[:19]}]:"
                            elements.append(Static(header, classes="assistant-header"))
                            
                            message = data.get('message', {})
                            content = self._extract_message_content(message)
                            if content.strip():
                                elements.append(Static(content, classes="assistant-content"))
                            else:
                                elements.append(Static("[No content or unable to extract]", classes="no-content"))
                            
                            # Add spacing
                            elements.append(Static("", classes="message-spacer"))
                        
                    except json.JSONDecodeError:
                        elements.append(Static(f"⚠️  Invalid JSON on line {line_num}", classes="error-message"))
            
            if not elements:
                elements.append(Static("No conversation content found.", classes="no-content"))
            
            return elements
            
        except Exception as e:
            return [Static(f"Error loading conversation: {e}", classes="error-message")]
    
    def _extract_message_content(self, message) -> str:
        """Extract text content from a message object"""
        if not isinstance(message, dict):
            return ""
        
        # First try to get content directly
        content = message.get('content', '')
        
        if isinstance(content, str) and content.strip():
            return content
        elif isinstance(content, list):
            # Extract content from list (Claude format)
            content_parts = []
            for item in content:
                if isinstance(item, dict):
                    item_type = item.get('type', '')
                    
                    if item_type == 'text':
                        # Regular text content
                        text = item.get('text', '')
                        if text.strip():
                            content_parts.append(text)
                    
                    elif item_type == 'tool_use':
                        # Tool use (function call)
                        name = item.get('name', 'unknown_tool')
                        input_data = item.get('input', {})
                        content_parts.append(f"🔧 Tool: {name}")
                        if input_data:
                            # Show tool input in a readable way
                            if isinstance(input_data, dict):
                                for key, value in input_data.items():
                                    content_parts.append(f"  {key}: {value}")
                            else:
                                content_parts.append(f"  Input: {input_data}")
                    
                    elif item_type == 'tool_result':
                        # Tool result - show only first 3 lines
                        tool_content = item.get('content', '')
                        if isinstance(tool_content, str) and tool_content.strip():
                            lines = tool_content.split('\n')
                            if len(lines) <= 3:
                                # Show all lines if 3 or fewer
                                content_parts.append(f"📋 Tool Result:\n{tool_content}")
                            else:
                                # Show first 3 lines with truncation indicator
                                first_lines = '\n'.join(lines[:3])
                                content_parts.append(f"📋 Tool Result:\n{first_lines}\n... ({len(lines)-3} more lines)")
                        elif tool_content:
                            content_parts.append(f"📋 Tool Result: {tool_content}")
                    
                    else:
                        # Unknown content type - try to extract any text
                        for field in ['text', 'content']:
                            if field in item:
                                value = item[field]
                                if isinstance(value, str) and value.strip():
                                    content_parts.append(value)
                                    break
            
            if content_parts:
                return '\n'.join(content_parts)
        
        # Try other common text fields
        for field in ['text', 'body']:
            if field in message:
                value = message[field]
                if isinstance(value, str) and value.strip():
                    return value
        
        # No content found
        return ""
    
    def action_back(self) -> None:
        self.app.pop_screen()
    
    def action_quit(self) -> None:
        self.app.exit()
    
    def action_rename(self) -> None:
        """Rename this conversation"""
        self._rename_dialog = RenameDialog(self.conversation.name)
        
        def callback(result):
            self._on_rename_complete(self._rename_dialog)
        
        self.app.push_screen(self._rename_dialog, callback)
    
    def action_delete(self) -> None:
        """Delete this conversation"""
        self._delete_dialog = ConfirmDialog(
            "Delete Conversation",
            f"Are you sure you want to delete '{self.conversation.name}'?"
        )
        
        def callback(result):
            self._on_delete_complete(self._delete_dialog)
        
        self.app.push_screen(self._delete_dialog, callback)
    
    def action_launch(self) -> None:
        """Launch Claude with this conversation"""
        self.app.launch_claude(self.conversation)
    
    def action_page_up(self) -> None:
        scroll = self.query_one("#conversation_scroll")
        scroll.scroll_up()
    
    def action_page_down(self) -> None:
        scroll = self.query_one("#conversation_scroll")
        scroll.scroll_down()
    
    def on_mouse_scroll_up(self, event) -> None:
        """Handle mouse wheel scroll up with 2x speed"""
        scroll = self.query_one("#conversation_scroll")
        scroll.scroll_up(animate=False)
        scroll.scroll_up(animate=False)  # 2x speed
    
    def on_mouse_scroll_down(self, event) -> None:
        """Handle mouse wheel scroll down with 2x speed"""
        scroll = self.query_one("#conversation_scroll")
        scroll.scroll_down(animate=False)
        scroll.scroll_down(animate=False)  # 2x speed
    
    def _on_rename_complete(self, dialog: RenameDialog) -> None:
        """Handle rename completion"""
        if dialog.new_name:
            with open("/tmp/shears_debug.log", "a") as f:
                f.write(f"DEBUG: Renaming conversation from '{self.conversation.name}' to '{dialog.new_name}'\n")
                f.write(f"DEBUG: Conversation ID in viewer: {id(self.conversation)}\n")
                f.write(f"DEBUG: Metadata file path: {self.conversation.metadata.metadata_path}\n")
            
            # CRITICAL FIX: Set the custom name (this automatically saves to disk)
            self.conversation.metadata.set_custom_name(dialog.new_name)
            
            # Update the conversation name so it shows correctly when going back
            self.conversation.name = dialog.new_name
            
            with open("/tmp/shears_debug.log", "a") as f:
                f.write(f"DEBUG: Updated conversation.name to '{self.conversation.name}'\n")
                f.write(f"DEBUG: set_custom_name() automatically saved to disk\n")
            # Update the viewer title to reflect the new name
            title_label = self.query_one("Label")
            title_label.update(f"Viewing: {dialog.new_name}")
            with open("/tmp/shears_debug.log", "a") as f:
                f.write("DEBUG: Updated viewer title\n")
    
    def _on_delete_complete(self, dialog: ConfirmDialog) -> None:
        """Handle delete completion"""
        if dialog.result:
            success = self.app.scanner.delete_conversation(self.conversation)
            if success:
                self.app.pop_screen()  # Go back to conversation list


class ConversationListView(ListView):
    """Custom ListView for conversations with proper key handling"""
    
    BINDINGS = [
        Binding("r", "rename", "Rename"),
        Binding("delete", "delete", "Delete"),
        Binding("enter", "select", "Preview"),
        Binding("escape", "back", "Back"),
        Binding("pageup", "page_up", "Page Up"),
        Binding("pagedown", "page_down", "Page Down"),
    ]
    
    def __init__(self, conversations: List[ConversationInfo], *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.conversations = conversations
    
    def action_rename(self) -> None:
        if self.index is not None and 0 <= self.index < len(self.conversations):
            conversation = self.conversations[self.index]
            self._rename_dialog = RenameDialog(conversation.name)
            
            def callback(result):
                self._on_rename_complete(self._rename_dialog)
            
            self.app.push_screen(self._rename_dialog, callback)
    
    def action_delete(self) -> None:
        if self.index is not None and 0 <= self.index < len(self.conversations):
            conversation = self.conversations[self.index]
            self._delete_dialog = ConfirmDialog(
                "Delete Conversation",
                f"Are you sure you want to delete '{conversation.name}'?"
            )
            
            def callback(result):
                self._on_delete_complete(self._delete_dialog)
            
            self.app.push_screen(self._delete_dialog, callback)
    
    def action_select(self) -> None:
        if self.index is not None and 0 <= self.index < len(self.conversations):
            conversation = self.conversations[self.index]
            self.app.view_conversation(conversation)
    
    def action_back(self) -> None:
        # Check if we're at the root conversation screen (launched from within project)
        # by checking if the current screen is the only non-main screen
        try:
            # Try to pop - if this is the last screen, it will go to a blank state
            # So we need to catch this case and show projects instead
            if hasattr(self.app, '_launched_from_project_dir') and self.app._launched_from_project_dir:
                # If launched from project dir, show project list instead of going back
                projects = self.app.scanner.scan_projects()
                self.app.push_screen(ProjectScreen(projects))
            else:
                self.app.pop_screen()
        except:
            # Fallback: show project list
            projects = self.app.scanner.scan_projects()
            self.app.push_screen(ProjectScreen(projects))
    
    def action_page_up(self) -> None:
        """Move selection up by page size"""
        if self.index is not None:
            page_size = max(1, self.size.height - 2)  # Account for borders
            new_index = max(0, self.index - page_size)
            self.action_select_cursor()
            for _ in range(self.index - new_index):
                self.action_cursor_up()
    
    def action_page_down(self) -> None:
        """Move selection down by page size"""
        if self.index is not None:
            page_size = max(1, self.size.height - 2)  # Account for borders
            new_index = min(len(self.conversations) - 1, self.index + page_size)
            self.action_select_cursor()
            for _ in range(new_index - self.index):
                self.action_cursor_down()
    
    def _on_rename_complete(self, dialog: RenameDialog) -> None:
        if dialog.new_name and self.index is not None:
            current_index = self.index
            conversation = self.conversations[self.index]
            conversation.metadata.set_custom_name(dialog.new_name)
            # Update the conversation name
            conversation.name = dialog.new_name
            
            # Update the specific list item in place
            if current_index < len(self.children):
                list_item = self.children[current_index]
                if hasattr(list_item, 'children') and len(list_item.children) > 0:
                    label = list_item.children[0]
                    label.update(self._format_conversation(conversation))
                    # Force a refresh of the display
                    self.refresh()
    
    def _on_delete_complete(self, dialog: ConfirmDialog) -> None:
        if dialog.result and self.index is not None:
            current_index = self.index
            conversation = self.conversations[self.index]
            success = self.app.scanner.delete_conversation(conversation)
            if success:
                # Remove from the local list
                del self.conversations[current_index]
                
                if self.conversations:
                    # Use ListView's pop method to remove the item
                    self.pop(current_index)
                    
                    # Handle selection after deletion
                    if current_index >= len(self.conversations):
                        # We deleted the last item, select the new last item
                        new_index = len(self.conversations) - 1
                        self.index = new_index
                    else:
                        # Keep the same index (now points to the next item)
                        self.index = current_index
                    
                    # Ensure index is valid and refresh
                    self.validate_index(self.index)
                    self.refresh()
                else:
                    # No conversations left, go back to project menu
                    self.app.pop_screen()
    
    def _format_conversation(self, conv: ConversationInfo) -> Text:
        """Format conversation for display"""
        date_str = format_date(conv.creation_date)
        msg_count = format_count(conv.message_count)
        return Text(f"{date_str}  {conv.name}  ({msg_count} messages)")


class ProjectListView(ListView):
    """Custom ListView for projects"""
    
    BINDINGS = [
        Binding("r", "rename", "Rename"),
        Binding("enter", "select", "Select"),
        Binding("pageup", "page_up", "Page Up"),
        Binding("pagedown", "page_down", "Page Down"),
        Binding("ctrl+c", "quit", "Quit"),
    ]
    
    def __init__(self, projects: List[ProjectInfo], *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.projects = projects
    
    def action_rename(self) -> None:
        if self.index is not None and 0 <= self.index < len(self.projects):
            project = self.projects[self.index]
            self.app.push_screen(RenameDialog(project.decoded_path), self._on_rename_complete)
    
    def action_select(self) -> None:
        if self.index is not None and 0 <= self.index < len(self.projects):
            project = self.projects[self.index]
            self.app.show_conversations(project)
    
    def action_quit(self) -> None:
        self.app.exit()
    
    def action_page_up(self) -> None:
        """Move selection up by page size"""
        if self.index is not None:
            page_size = max(1, self.size.height - 2)  # Account for borders
            new_index = max(0, self.index - page_size)
            self.action_select_cursor()
            for _ in range(self.index - new_index):
                self.action_cursor_up()
    
    def action_page_down(self) -> None:
        """Move selection down by page size"""
        if self.index is not None:
            page_size = max(1, self.size.height - 2)  # Account for borders
            new_index = min(len(self.projects) - 1, self.index + page_size)
            self.action_select_cursor()
            for _ in range(new_index - self.index):
                self.action_cursor_down()
    
    def _on_rename_complete(self, dialog: RenameDialog) -> None:
        if dialog.new_name and self.index is not None:
            project = self.projects[self.index]
            success = self.app.scanner.rename_project(project, dialog.new_name)
            if success:
                # Update the project's decoded path
                project.decoded_path = dialog.new_name
                # Update the list item
                list_item = self.children[self.index]
                list_item.children[0].update(self._format_project(project))
    
    def _format_project(self, project: ProjectInfo) -> Text:
        """Format project for display"""
        date_str = format_date(project.creation_date)
        conv_count = format_count(project.conversation_count)
        msg_count = format_count(project.total_messages)
        path = project.decoded_path
        
        return Text(f"{date_str}  {path}  ({conv_count} conversations, {msg_count} messages)")


class ConversationScreen(Screen):
    """Screen showing conversations for a specific project"""
    
    BINDINGS = [
        Binding("ctrl+c", "quit", "Quit"),
    ]
    
    def __init__(self, project: ProjectInfo):
        super().__init__()
        self.project = project
    
    def compose(self) -> ComposeResult:
        decoded_path = self.project.decoded_path
        title = f"Conversations - {decoded_path}"
        
        hotkeys = "R=Rename  Del=Delete  Enter=View/Launch  Esc=Back  Ctrl+C=Quit"
        
        yield Header(show_clock=False)
        yield Label(title, classes="screen-title")
        yield ConversationListView(
            self.project.conversations,
            *[
                ListItem(Label(self._format_conversation(conv)))
                for conv in self.project.conversations
            ]
        )
        yield Label(hotkeys, classes="hotkeys")
    
    def on_mount(self) -> None:
        """Set focus to the conversation list when mounted"""
        self.call_after_refresh(self._set_focus)
    
    def _set_focus(self) -> None:
        """Set focus to the ListView after refresh"""
        try:
            self.query_one(ConversationListView).focus()
        except Exception:
            pass
    
    def _format_conversation(self, conv: ConversationInfo) -> Text:
        """Format conversation for display"""
        date_str = format_date(conv.creation_date)
        msg_count = format_count(conv.message_count)
        return Text(f"{date_str}  {conv.name}  ({msg_count} messages)")
    
    def on_resume(self) -> None:
        """Called when this screen is resumed - refresh the conversation list"""
        with open("/tmp/shears_debug.log", "a") as f:
            f.write("DEBUG: ConversationScreen.on_resume called - forcing complete rebuild\n")
        self._refresh_conversation_list()
    
    def on_show(self) -> None:
        """Called when this screen is shown - refresh the conversation list"""  
        with open("/tmp/shears_debug.log", "a") as f:
            f.write("DEBUG: ConversationScreen.on_show called - forcing complete rebuild\n")
        self._refresh_conversation_list()
    
    def on_screen_resume(self) -> None:
        """Called when screen resumes focus"""
        with open("/tmp/shears_debug.log", "a") as f:
            f.write("DEBUG: ConversationScreen.on_screen_resume called - forcing complete rebuild\n")
        self._refresh_conversation_list()
    
    def _refresh_conversation_list(self) -> None:
        """Refresh the conversation list by rebuilding it"""
        # BRUTE FORCE: Remove the old ListView and create a new one
        try:
            old_list = self.query_one(ConversationListView)
            old_index = old_list.index if old_list.index is not None else 0
            old_list.remove()
            
            # Force reload names from metadata
            for i, conv in enumerate(self.project.conversations):
                old_name = conv.name
                # Force reload metadata from disk
                conv.metadata._metadata = conv.metadata._load_metadata()
                conv.name = conv.metadata.name
                with open("/tmp/shears_debug.log", "a") as f:
                    f.write(f"DEBUG: Reloading conv {i}: '{old_name}' -> '{conv.name}' (metadata says: '{conv.metadata.name}')\n")
            
            # Create completely new ListView
            with open("/tmp/shears_debug.log", "a") as f:
                f.write("DEBUG: Creating new ListView with these conversation names:\n")
                for i, conv in enumerate(self.project.conversations):
                    f.write(f"DEBUG:   {i}: '{conv.name}' (id: {id(conv)})\n")
            
            new_list = ConversationListView(
                self.project.conversations,
                *[
                    ListItem(Label(self._format_conversation(conv)))
                    for conv in self.project.conversations
                ]
            )
            
            # Mount the new list before the hotkeys
            self.mount(new_list, before=self.query_one(".hotkeys"))
            
            # Restore selection
            if old_index < len(self.project.conversations):
                new_list.index = old_index
                
            with open("/tmp/shears_debug.log", "a") as f:
                f.write("DEBUG: Completely rebuilt ListView\n")
                
        except Exception as e:
            with open("/tmp/shears_debug.log", "a") as f:
                f.write(f"DEBUG: Error rebuilding ListView: {e}\n")
    
    def action_quit(self) -> None:
        self.app.exit()


class ProjectScreen(Screen):
    """Screen showing all projects"""
    
    BINDINGS = [
        Binding("ctrl+c", "quit", "Quit"),
    ]
    
    def __init__(self, projects: List[ProjectInfo]):
        super().__init__()
        self.projects = projects
    
    def compose(self) -> ComposeResult:
        title = "Claude Projects"
        hotkeys = "R=Rename  Enter=Select  Ctrl+C=Quit"
        
        yield Header(show_clock=False)
        yield Label(title, classes="screen-title")
        yield ProjectListView(
            self.projects,
            *[
                ListItem(Label(self._format_project(project)))
                for project in self.projects
            ]
        )
        yield Label(hotkeys, classes="hotkeys")
    
    def on_mount(self) -> None:
        """Set focus to the project list when mounted"""
        self.call_after_refresh(self._set_focus)
    
    def _set_focus(self) -> None:
        """Set focus to the ListView after refresh"""
        try:
            self.query_one(ProjectListView).focus()
        except Exception:
            pass
    
    def _format_project(self, project: ProjectInfo) -> Text:
        """Format project for display"""
        date_str = format_date(project.creation_date)
        conv_count = format_count(project.conversation_count)
        msg_count = format_count(project.total_messages)
        path = project.decoded_path
        
        return Text(f"{date_str}  {path}  ({conv_count} conversations, {msg_count} messages)")
    
    def action_quit(self) -> None:
        self.app.exit()


class ShearsApp(App):
    """Main Shears application"""
    
    CSS = """
    .screen-title {
        text-align: center;
        padding: 1;
        background: $primary;
        color: $text;
    }
    
    .hotkeys {
        dock: bottom;
        height: 1;
        background: $surface;
        color: $text;
        text-align: center;
    }
    
    .dialog {
        align: center middle;
        width: 60;
        height: auto;
        background: $surface;
        border: solid $primary;
        padding: 1;
    }
    
    .dialog-title {
        text-align: center;
        text-style: bold;
        padding-bottom: 1;
    }
    
    .dialog-message {
        text-align: center;
        padding-bottom: 1;
    }
    
    .dialog-help {
        text-align: center;
        color: $text-muted;
    }
    
    ListView {
        margin: 1;
    }
    
    ListItem {
        padding: 0 1;
    }
    
    ScrollableContainer {
        scrollbar-size-vertical: 3;
    }
    
    ListView {
        scrollbar-size-vertical: 3;
    }
    
    """
    
    def __init__(self):
        super().__init__()
        self.scanner = ProjectScanner()
        self._launch_cmd = None
        self._launch_cwd = None
        self._launched_from_project_dir = False
    
    def on_mount(self) -> None:
        """Initialize the application"""
        projects = self.scanner.scan_projects()
        
        # Check if current directory has a project
        current_project = self.scanner.get_current_working_directory_project()
        if current_project:
            self._launched_from_project_dir = True
            self.show_conversations(current_project)
        else:
            self.push_screen(ProjectScreen(projects))
    
    def show_conversations(self, project: ProjectInfo) -> None:
        """Show conversations for a project"""
        self.push_screen(ConversationScreen(project))
    
    def view_conversation(self, conversation: ConversationInfo) -> None:
        """View conversation content"""
        self.push_screen(ConversationViewer(conversation))
    
    def launch_claude(self, conversation: ConversationInfo) -> None:
        """Launch Claude CLI with the specified conversation"""
        try:
            # Get the project info to determine working directory
            project = None
            for p in self.scanner._projects or []:
                if conversation in p.conversations:
                    project = p
                    break
            
            if project:
                working_dir = project.working_path
                # If the working path doesn't exist, prompt user for correction
                if not os.path.exists(working_dir):
                    self._prompt_path_correction(project, conversation)
                    return
            else:
                working_dir = os.getcwd()
            
            # Store launch info for after TUI exit
            self._launch_cmd = ["claude", "--resume", conversation.session_id]
            self._launch_cwd = working_dir
            
            # Exit the TUI - launch will happen in main()
            self.exit()
            
        except Exception as e:
            # Exit with error - in a real app we could show the error
            self.exit(return_code=1)
    
    def _prompt_path_correction(self, project: ProjectInfo, conversation: ConversationInfo) -> None:
        """Prompt user to correct the project path"""
        self._path_dialog = PathCorrectionDialog(project.working_path, project.decoded_path)
        self._path_project = project
        self._path_conversation = conversation
        
        def callback(result):
            self._on_path_correction_complete(self._path_dialog, self._path_project, self._path_conversation)
        
        self.push_screen(self._path_dialog, callback)
    
    def _on_path_correction_complete(self, dialog: PathCorrectionDialog, project: ProjectInfo, conversation: ConversationInfo) -> None:
        """Handle path correction completion"""
        if dialog and hasattr(dialog, 'corrected_path') and dialog.corrected_path:
            # Save the corrected path
            success = self.scanner.set_project_path(project, dialog.corrected_path)
            if success:
                # Update the project's working path
                project.working_path = dialog.corrected_path
                # Now launch Claude with the corrected path
                self._launch_cmd = ["claude", "--resume", conversation.session_id]
                self._launch_cwd = dialog.corrected_path
                self.exit()
            else:
                # Could show error, for now just exit
                self.exit(return_code=1)
        # If user cancelled, just do nothing (stay in the TUI)


def main():
    """Main entry point"""
    app = ShearsApp()
    app.run()
    
    # Check if we need to launch Claude after TUI exit
    if hasattr(app, '_launch_cmd') and hasattr(app, '_launch_cwd'):
        try:
            subprocess.run(app._launch_cmd, cwd=app._launch_cwd)
        except Exception:
            pass


if __name__ == "__main__":
    main()