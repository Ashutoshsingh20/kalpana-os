#!/usr/bin/env python3
"""
Kalpana OS - File Management Tools
===================================
Cross-platform file operations.
"""

import os
import shutil
from pathlib import Path
from typing import Dict, Any, List


class FileTool:
    """File system operations and organization."""
    
    def __init__(self):
        self.extensions_map = {
            "Images": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg", ".webp", ".ico"],
            "Videos": [".mp4", ".mkv", ".avi", ".mov", ".wmv", ".flv", ".webm"],
            "Audio": [".mp3", ".wav", ".flac", ".aac", ".ogg", ".m4a"],
            "Documents": [".pdf", ".doc", ".docx", ".txt", ".rtf", ".odt", ".xls", ".xlsx"],
            "Archives": [".zip", ".rar", ".7z", ".tar", ".gz", ".bz2"],
            "Code": [".py", ".js", ".html", ".css", ".java", ".cpp", ".c", ".rs", ".go"],
            "Data": [".json", ".xml", ".csv", ".sql", ".db"],
        }

    async def list_directory(self, path: str) -> str:
        """List contents of a directory."""
        p = Path(path).expanduser()
        if not p.exists():
            return f"❌ Path not found: {path}"
            
        if not p.is_dir():
            return f"❌ Not a directory: {path}"
        
        items = []
        for item in sorted(p.iterdir()):
            if item.is_dir():
                items.append(f"📁 {item.name}/")
            else:
                size = item.stat().st_size
                if size < 1024:
                    size_str = f"{size}B"
                elif size < 1024 * 1024:
                    size_str = f"{size/1024:.1f}KB"
                else:
                    size_str = f"{size/1024/1024:.1f}MB"
                items.append(f"📄 {item.name} ({size_str})")
        
        return f"**Contents of {path}:**\n" + "\n".join(items[:50])

    async def move_file(self, src: str, dst: str) -> str:
        """Move a file from source to destination."""
        src_path = Path(src).expanduser()
        dst_path = Path(dst).expanduser()
        
        if not src_path.exists():
            return f"❌ Source not found: {src}"
        
        try:
            # Create destination directory if needed
            if dst_path.is_dir():
                dst_path = dst_path / src_path.name
            else:
                dst_path.parent.mkdir(parents=True, exist_ok=True)
            
            shutil.move(str(src_path), str(dst_path))
            return f"✅ Moved {src_path.name} to {dst_path}"
        except Exception as e:
            return f"❌ Error moving file: {e}"

    async def copy_file(self, src: str, dst: str) -> str:
        """Copy a file."""
        src_path = Path(src).expanduser()
        dst_path = Path(dst).expanduser()
        
        if not src_path.exists():
            return f"❌ Source not found: {src}"
        
        try:
            if src_path.is_dir():
                shutil.copytree(str(src_path), str(dst_path))
            else:
                if dst_path.is_dir():
                    dst_path = dst_path / src_path.name
                shutil.copy2(str(src_path), str(dst_path))
            return f"✅ Copied to {dst_path}"
        except Exception as e:
            return f"❌ Error copying: {e}"

    async def organize_directory(self, path: str) -> str:
        """Organize files into subfolders based on type."""
        p = Path(path).expanduser()
        if not p.exists() or not p.is_dir():
            return f"❌ Invalid directory: {path}"
        
        moved = 0
        for item in p.iterdir():
            if item.is_file():
                ext = item.suffix.lower()
                folder = "Other"
                
                for category, extensions in self.extensions_map.items():
                    if ext in extensions:
                        folder = category
                        break
                
                target_dir = p / folder
                target_dir.mkdir(exist_ok=True)
                
                try:
                    shutil.move(str(item), str(target_dir / item.name))
                    moved += 1
                except:
                    pass
        
        return f"✅ Organized {moved} files into categories"

    async def find_files(self, pattern: str, path: str = "~") -> str:
        """Find files matching a pattern."""
        p = Path(path).expanduser()
        if not p.exists():
            return f"❌ Path not found: {path}"
        
        matches = []
        try:
            for item in p.rglob(pattern):
                matches.append(str(item))
                if len(matches) >= 50:
                    break
        except PermissionError:
            pass
        
        if not matches:
            return f"No files matching '{pattern}' found"
        
        return f"**Found {len(matches)} files:**\n" + "\n".join(matches)

    async def write_to_file(self, path: str, content: str) -> str:
        """Write content to a file."""
        p = Path(path).expanduser()
        
        try:
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(content)
            return f"✅ Wrote {len(content)} bytes to {path}"
        except Exception as e:
            return f"❌ Error writing file: {e}"

    async def read_file(self, path: str) -> str:
        """Read content from a file."""
        p = Path(path).expanduser()
        
        if not p.exists():
            return f"❌ File not found: {path}"
        
        try:
            content = p.read_text()
            if len(content) > 5000:
                content = content[:5000] + "\n\n... (truncated)"
            return f"**Contents of {p.name}:**\n```\n{content}\n```"
        except Exception as e:
            return f"❌ Error reading file: {e}"

    async def delete_file(self, path: str) -> str:
        """Delete a file or directory."""
        p = Path(path).expanduser()
        
        if not p.exists():
            return f"❌ Path not found: {path}"
        
        try:
            if p.is_dir():
                shutil.rmtree(str(p))
            else:
                p.unlink()
            return f"✅ Deleted {path}"
        except Exception as e:
            return f"❌ Error deleting: {e}"

    async def get_disk_usage(self, path: str = "/") -> str:
        """Get disk usage for a path."""
        p = Path(path).expanduser()
        
        try:
            usage = shutil.disk_usage(str(p))
            total_gb = usage.total / (1024**3)
            used_gb = usage.used / (1024**3)
            free_gb = usage.free / (1024**3)
            percent = (usage.used / usage.total) * 100
            
            return f"""**Disk Usage for {path}:**
- Total: {total_gb:.1f} GB
- Used: {used_gb:.1f} GB ({percent:.1f}%)
- Free: {free_gb:.1f} GB"""
        except Exception as e:
            return f"❌ Error: {e}"


# Global instance
_file_tool = FileTool()


def get_file_tools() -> Dict[str, Dict[str, Any]]:
    """Get file tools for registration."""
    return {
        "list_directory": {
            "func": _file_tool.list_directory,
            "description": "List contents of a directory",
            "parameters": {"path": {"type": "string", "description": "Directory path"}},
            "category": "files"
        },
        "move_file": {
            "func": _file_tool.move_file,
            "description": "Move a file from source to destination",
            "parameters": {
                "src": {"type": "string", "description": "Source path"},
                "dst": {"type": "string", "description": "Destination path"}
            },
            "category": "files"
        },
        "copy_file": {
            "func": _file_tool.copy_file,
            "description": "Copy a file or directory",
            "parameters": {
                "src": {"type": "string", "description": "Source path"},
                "dst": {"type": "string", "description": "Destination path"}
            },
            "category": "files"
        },
        "organize_directory": {
            "func": _file_tool.organize_directory,
            "description": "Organize files into folders by type",
            "parameters": {"path": {"type": "string", "description": "Directory to organize"}},
            "category": "files"
        },
        "find_files": {
            "func": _file_tool.find_files,
            "description": "Find files matching a pattern",
            "parameters": {
                "pattern": {"type": "string", "description": "Search pattern (e.g., *.pdf)"},
                "path": {"type": "string", "description": "Search directory"}
            },
            "category": "files"
        },
        "write_to_file": {
            "func": _file_tool.write_to_file,
            "description": "Write content to a file",
            "parameters": {
                "path": {"type": "string", "description": "File path"},
                "content": {"type": "string", "description": "Content to write"}
            },
            "category": "files"
        },
        "read_file": {
            "func": _file_tool.read_file,
            "description": "Read content from a file",
            "parameters": {"path": {"type": "string", "description": "File path"}},
            "category": "files"
        },
        "delete_file": {
            "func": _file_tool.delete_file,
            "description": "Delete a file or directory",
            "parameters": {"path": {"type": "string", "description": "Path to delete"}},
            "category": "files",
            "side_effects": ["destructive"]
        },
        "get_disk_usage": {
            "func": _file_tool.get_disk_usage,
            "description": "Get disk usage information",
            "parameters": {"path": {"type": "string", "description": "Path to check"}},
            "category": "system"
        }
    }
