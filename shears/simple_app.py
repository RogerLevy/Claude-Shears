"""
Simple text-based interface for shears (fallback when TUI doesn't work well)
"""

import os
import sys
import subprocess
from .scanner import ProjectScanner
from .utils import format_date, format_count


class SimpleShears:
    """Simple text-based interface for shears"""
    
    def __init__(self):
        self.scanner = ProjectScanner()
        self.current_project = None
    
    def run(self):
        """Main entry point"""
        try:
            projects = self.scanner.scan_projects()
            # Always start with project selection menu
            self.show_projects(projects)
        except KeyboardInterrupt:
            print("\nGoodbye!")
            sys.exit(0)
        except EOFError:
            print("\nGoodbye!")
            sys.exit(0)
    
    def show_projects(self, projects):
        """Show project selection menu"""
        while True:
            print("\n" + "="*60)
            print("=== Shears - Claude Project Manager ===")
            print("="*60)
            
            if not projects:
                print("No projects found in ~/.claude/projects")
                return
            
            print("Projects:")
            for i, project in enumerate(projects, 1):
                date_str = format_date(project.creation_date)
                conv_count = format_count(project.conversation_count)
                msg_count = format_count(project.total_messages)
                print(f"{i:2}. {date_str}  {project.decoded_path}")
                print(f"    ({conv_count} conversations, {msg_count} messages)")
            
            print(f"\nEnter project number (1-{len(projects)}) or 'q' to quit: ", end='')
            
            try:
                choice = input().strip()
                if choice.lower() == 'q':
                    break
                
                project_num = int(choice)
                if 1 <= project_num <= len(projects):
                    self.show_conversations(projects[project_num - 1])
                else:
                    print("Invalid selection. Press Enter to continue...")
                    input()
            except ValueError:
                print("Please enter a number. Press Enter to continue...")
                input()
            except (KeyboardInterrupt, EOFError):
                break
    
    def show_conversations(self, project):
        """Show conversations for a project"""
        while True:
            print("\n" + "="*80)
            print(f"=== Conversations - {project.decoded_path} ===")
            print("="*80)
            
            conversations = project.conversations
            if not conversations:
                print("No conversations found in this project")
                input("Press Enter to go back...")
                return
            
            print("Conversations:")
            for i, conv in enumerate(conversations, 1):
                date_str = format_date(conv.creation_date)
                msg_count = format_count(conv.message_count)
                name = conv.name[:60] + "..." if len(conv.name) > 60 else conv.name
                print(f"{i:2}. {date_str}  {name}")
                print(f"    ({msg_count} messages)")
            
            print(f"\nOptions:")
            print(f"  1-{len(conversations)}: Select conversation to launch")
            print(f"  r<num>: Rename conversation (e.g., 'r1')")
            print(f"  d<num>: Delete conversation (e.g., 'd1')")
            print(f"  b: Back to projects")
            print(f"  q: Quit")
            print(f"\nChoice: ", end='')
            
            try:
                choice = input().strip().lower()
                
                if choice == 'q':
                    sys.exit(0)
                elif choice == 'b':
                    return
                elif choice.startswith('r') and len(choice) > 1:
                    # Rename conversation
                    try:
                        conv_num = int(choice[1:])
                        if 1 <= conv_num <= len(conversations):
                            self.rename_conversation(conversations[conv_num - 1])
                        else:
                            print("Invalid conversation number. Press Enter to continue...")
                            input()
                    except ValueError:
                        print("Invalid format. Use 'r<number>'. Press Enter to continue...")
                        input()
                elif choice.startswith('d') and len(choice) > 1:
                    # Delete conversation
                    try:
                        conv_num = int(choice[1:])
                        if 1 <= conv_num <= len(conversations):
                            if self.delete_conversation(conversations[conv_num - 1]):
                                return  # Go back to refresh the list
                        else:
                            print("Invalid conversation number. Press Enter to continue...")
                            input()
                    except ValueError:
                        print("Invalid format. Use 'd<number>'. Press Enter to continue...")
                        input()
                else:
                    # Launch conversation
                    try:
                        conv_num = int(choice)
                        if 1 <= conv_num <= len(conversations):
                            self.launch_conversation(conversations[conv_num - 1], project)
                            return
                        else:
                            print("Invalid selection. Press Enter to continue...")
                            input()
                    except ValueError:
                        print("Invalid input. Press Enter to continue...")
                        input()
            except (KeyboardInterrupt, EOFError):
                return
    
    def rename_conversation(self, conversation):
        """Rename a conversation"""
        print(f"\nCurrent name: {conversation.name}")
        print("New name (or Enter to cancel): ", end='')
        try:
            new_name = input().strip()
            if new_name:
                conversation.metadata.set_custom_name(new_name)
                conversation.name = new_name
                print("Conversation renamed successfully!")
            else:
                print("Rename cancelled.")
            input("Press Enter to continue...")
        except (KeyboardInterrupt, EOFError):
            print("\nRename cancelled.")
            try:
                input("Press Enter to continue...")
            except (KeyboardInterrupt, EOFError):
                pass
    
    def delete_conversation(self, conversation):
        """Delete a conversation with confirmation"""
        print(f"\nDelete conversation: {conversation.name}")
        print("Type 'DELETE' to confirm: ", end='')
        try:
            confirmation = input().strip()
            if confirmation == 'DELETE':
                success = self.scanner.delete_conversation(conversation)
                if success:
                    print("Conversation deleted successfully!")
                    input("Press Enter to continue...")
                    return True
                else:
                    print("Failed to delete conversation.")
                    input("Press Enter to continue...")
            else:
                print("Deletion cancelled.")
                input("Press Enter to continue...")
        except (KeyboardInterrupt, EOFError):
            print("\nDeletion cancelled.")
            try:
                input("Press Enter to continue...")
            except (KeyboardInterrupt, EOFError):
                pass
        return False
    
    def launch_conversation(self, conversation, project):
        """Launch Claude CLI with the conversation"""
        try:
            working_dir = project.decoded_path
            cmd = ["claude", "--resume", conversation.session_id]
            
            print(f"\nLaunching Claude in {working_dir}")
            print(f"Command: {' '.join(cmd)}")
            print("Press Enter to continue...")
            input()
            
            # Change to working directory and launch
            os.chdir(working_dir)
            os.execvp("claude", cmd)
            
        except Exception as e:
            print(f"Error launching Claude: {e}")
            input("Press Enter to continue...")


def main():
    """Main entry point for simple app"""
    app = SimpleShears()
    app.run()


if __name__ == "__main__":
    main()