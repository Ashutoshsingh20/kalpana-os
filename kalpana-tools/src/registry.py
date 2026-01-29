#!/usr/bin/env python3
"""
Kalpana OS - Tool Registry
===========================
Unified registry for all Kalpana tools.
"""

from typing import Dict, Any, Callable


class ToolRegistry:
    """Central registry for all Kalpana tools."""
    
    def __init__(self):
        self.tools: Dict[str, Dict[str, Any]] = {}
        self.categories: Dict[str, list] = {}
    
    def register(self, name: str, tool: Dict[str, Any]):
        """Register a tool."""
        self.tools[name] = tool
        
        category = tool.get("category", "general")
        if category not in self.categories:
            self.categories[category] = []
        self.categories[category].append(name)
    
    def register_all(self, tools: Dict[str, Dict[str, Any]]):
        """Register multiple tools."""
        for name, tool in tools.items():
            self.register(name, tool)
    
    def get(self, name: str) -> Dict[str, Any]:
        """Get a tool by name."""
        return self.tools.get(name)
    
    def get_func(self, name: str) -> Callable:
        """Get a tool's function."""
        tool = self.tools.get(name)
        return tool.get("func") if tool else None
    
    def list_tools(self) -> Dict[str, list]:
        """List all tools by category."""
        return self.categories
    
    def search(self, query: str) -> list:
        """Search tools by name or description."""
        query = query.lower()
        matches = []
        
        for name, tool in self.tools.items():
            if query in name.lower() or query in tool.get("description", "").lower():
                matches.append(name)
        
        return matches
    
    def get_tool_info(self, name: str) -> str:
        """Get formatted tool information."""
        tool = self.tools.get(name)
        if not tool:
            return f"Tool '{name}' not found"
        
        params = tool.get("parameters", {})
        param_str = ", ".join([
            f"{k}: {v.get('type', 'any')}"
            for k, v in params.items()
        ]) if params else "none"
        
        return f"""**{name}**
Category: {tool.get('category', 'general')}
Description: {tool.get('description', 'No description')}
Parameters: {param_str}"""


def create_registry() -> ToolRegistry:
    """Create and populate the tool registry."""
    registry = ToolRegistry()
    
    # Import and register all tool modules
    try:
        from .linux_system import get_linux_system_tools
        registry.register_all(get_linux_system_tools())
    except ImportError:
        pass
    
    try:
        from .files import get_file_tools
        registry.register_all(get_file_tools())
    except ImportError:
        pass
    
    try:
        from .productivity import get_productivity_tools
        registry.register_all(get_productivity_tools())
    except ImportError:
        pass
    
    try:
        from .calendar_tools import get_calendar_tools
        registry.register_all(get_calendar_tools())
    except ImportError:
        pass
    
    try:
        from .vision import get_vision_tools
        registry.register_all(get_vision_tools())
    except ImportError:
        pass
    
    try:
        from .voice import get_voice_tools
        registry.register_all(get_voice_tools())
    except ImportError:
        pass
    
    try:
        from .media import get_media_tools
        registry.register_all(get_media_tools())
    except ImportError:
        pass
    
    try:
        from .brain import get_brain_tools
        registry.register_all(get_brain_tools())
    except ImportError:
        pass
    
    return registry


# Global registry
_registry = None

def get_registry() -> ToolRegistry:
    """Get the global tool registry."""
    global _registry
    if _registry is None:
        _registry = create_registry()
    return _registry


async def execute_tool(tool_name: str, **kwargs) -> Any:
    """Execute a tool by name."""
    registry = get_registry()
    func = registry.get_func(tool_name)
    
    if not func:
        return f"Tool '{tool_name}' not found"
    
    try:
        result = await func(**kwargs)
        return result
    except Exception as e:
        return f"Error executing {tool_name}: {e}"


def list_all_tools() -> str:
    """List all available tools."""
    registry = get_registry()
    output = "**🔧 Available Tools:**\n\n"
    
    for category, tools in sorted(registry.categories.items()):
        output += f"**{category.title()}:**\n"
        for tool_name in tools:
            tool = registry.get(tool_name)
            output += f"  - `{tool_name}`: {tool.get('description', '')[:50]}\n"
        output += "\n"
    
    return output
