#!/usr/bin/env python3
"""
Kalpana OS - Productivity Tools
================================
Todo, Notes, and Productivity management for Linux.
"""

import json
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid


# Data directories
DATA_DIR = Path.home() / ".kalpana" / "data"
TODO_FILE = DATA_DIR / "todos.json"
NOTES_DIR = DATA_DIR / "notes"

# Ensure directories exist
DATA_DIR.mkdir(parents=True, exist_ok=True)
NOTES_DIR.mkdir(parents=True, exist_ok=True)


class TodoManager:
    """Todo list manager."""
    
    def __init__(self):
        self._load()

    def _load(self):
        if TODO_FILE.exists():
            try:
                with open(TODO_FILE, 'r') as f:
                    self.todos = json.load(f)
            except:
                self.todos = []
        else:
            self.todos = []

    def _save(self):
        with open(TODO_FILE, 'w') as f:
            json.dump(self.todos, f, indent=2)

    async def add_task(self, task: str, priority: str = "medium") -> str:
        """Add a new task."""
        if not task:
            return "Task cannot be empty"
            
        new_task = {
            "id": str(uuid.uuid4())[:8],
            "task": task,
            "priority": priority,
            "status": "pending",
            "created_at": datetime.now().isoformat()
        }
        self.todos.append(new_task)
        self._save()
        return f"✅ Added task: {task} (ID: {new_task['id']})"

    async def list_tasks(self, status: str = "pending") -> str:
        """List tasks by status (pending/completed/all)."""
        self._load()
        
        if status == "all":
            filtered = self.todos
        else:
            filtered = [t for t in self.todos if t["status"] == status]
            
        if not filtered:
            return f"No {status} tasks found."
            
        output = f"**{status.title()} Tasks:**\n"
        for t in filtered:
            icon = "⬜" if t['status'] == 'pending' else "✅"
            output += f"{icon} `{t['id']}`: {t['task']} ({t.get('priority', 'medium')})\n"
            
        return output

    async def complete_task(self, task_id_or_keyword: str) -> str:
        """Mark a task as complete."""
        self._load()
        target = None
        
        # Try exact ID match
        for t in self.todos:
            if t['id'] == task_id_or_keyword:
                target = t
                break
        
        # Try keyword match
        if not target:
            matches = [t for t in self.todos 
                      if task_id_or_keyword.lower() in t['task'].lower() 
                      and t['status'] == 'pending']
            if len(matches) == 1:
                target = matches[0]
            elif len(matches) > 1:
                return f"⚠️ Multiple tasks match. Be more specific."
                
        if target:
            target['status'] = 'completed'
            target['completed_at'] = datetime.now().isoformat()
            self._save()
            return f"✅ Completed: {target['task']}"
            
        return f"❌ Task not found: {task_id_or_keyword}"

    async def remove_task(self, task_id: str) -> str:
        """Remove a task."""
        self._load()
        initial_len = len(self.todos)
        self.todos = [t for t in self.todos if t['id'] != task_id]
        
        if len(self.todos) < initial_len:
            self._save()
            return f"Removed task {task_id}"
        return f"Task {task_id} not found"


class NotesManager:
    """Notes manager."""
    
    async def create_note(self, title: str, content: str) -> str:
        """Create a new note."""
        filename = "".join([c for c in title if c.isalnum() or c in (' ', '-', '_')]).strip()
        filename = filename.replace(" ", "_") + ".md"
        
        filepath = NOTES_DIR / filename
        
        if filepath.exists():
            return f"⚠️ Note '{filename}' exists. Use append_note."
            
        with open(filepath, 'w') as f:
            f.write(f"# {title}\n\n{content}")
            
        return f"📝 Note created: {filename}"

    async def read_note(self, title_keyword: str) -> str:
        """Read a note."""
        found = list(NOTES_DIR.glob(f"*{title_keyword}*"))
        if not found:
            return f"❌ No note found matching '{title_keyword}'"
        
        filepath = found[0]
        with open(filepath, 'r') as f:
            content = f.read()
            
        return f"**📄 {filepath.name}**\n\n{content}"

    async def list_notes(self) -> str:
        """List all notes."""
        notes = list(NOTES_DIR.glob("*.md"))
        if not notes:
            return "No notes found."
            
        output = "**Saved Notes:**\n"
        for n in notes:
            output += f"- {n.stem}\n"
        return output
        
    async def append_note(self, title_keyword: str, content: str) -> str:
        """Append to an existing note."""
        found = list(NOTES_DIR.glob(f"*{title_keyword}*"))
        if not found:
            return f"❌ No note found matching '{title_keyword}'"
            
        filepath = found[0]
        with open(filepath, 'a') as f:
            f.write(f"\n\n{content}")
            
        return f"✅ Added to note: {filepath.stem}"


# Global instances
_todo_mgr = TodoManager()
_notes_mgr = NotesManager()


def get_productivity_tools() -> Dict[str, Dict[str, Any]]:
    """Get productivity tools for registration."""
    return {
        "add_task": {
            "func": _todo_mgr.add_task,
            "description": "Add a new task to the To-Do list",
            "parameters": {
                "task": {"type": "string", "description": "Task description"},
                "priority": {"type": "string", "description": "low, medium, high"}
            },
            "category": "productivity"
        },
        "list_tasks": {
            "func": _todo_mgr.list_tasks,
            "description": "List tasks (pending/completed/all)",
            "parameters": {
                "status": {"type": "string", "description": "pending, completed, or all"}
            },
            "category": "productivity"
        },
        "complete_task": {
            "func": _todo_mgr.complete_task,
            "description": "Mark a task as completed",
            "parameters": {
                "task_id_or_keyword": {"type": "string", "description": "ID or keyword"}
            },
            "category": "productivity"
        },
        "remove_task": {
            "func": _todo_mgr.remove_task,
            "description": "Remove a task",
            "parameters": {"task_id": {"type": "string", "description": "Task ID"}},
            "category": "productivity"
        },
        "create_note": {
            "func": _notes_mgr.create_note,
            "description": "Create a new note",
            "parameters": {
                "title": {"type": "string", "description": "Note title"},
                "content": {"type": "string", "description": "Note content"}
            },
            "category": "productivity"
        },
        "read_note": {
            "func": _notes_mgr.read_note,
            "description": "Read a note",
            "parameters": {
                "title_keyword": {"type": "string", "description": "Title or keyword"}
            },
            "category": "productivity"
        },
        "list_notes": {
            "func": _notes_mgr.list_notes,
            "description": "List all saved notes",
            "parameters": {},
            "category": "productivity"
        },
        "append_note": {
            "func": _notes_mgr.append_note,
            "description": "Append to an existing note",
            "parameters": {
                "title_keyword": {"type": "string", "description": "Note to update"},
                "content": {"type": "string", "description": "Content to add"}
            },
            "category": "productivity"
        }
    }
