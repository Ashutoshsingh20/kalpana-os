#!/usr/bin/env python3
"""
Kalpana Shell
=============
AI-native shell replacing bash.
All commands pass through Kalpana Core for policy enforcement.
"""

import asyncio
import os
import sys
import subprocess
import readline
from typing import Optional
from datetime import datetime

# Add parent to path for ipc_client
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'kalpana-core', 'src'))

try:
    from ipc_client import KalpanaIPCClient
except ImportError:
    # Fallback if not in expected location
    class KalpanaIPCClient:
        def __init__(self, dev_mode=True):
            self.dev_mode = dev_mode
        async def connect(self): return False
        async def execute(self, cmd): return {"allowed": True, "decision": "allow"}
        async def get_status(self): return {"status": "standalone"}
        async def get_audit_log(self): return {"entries": []}
        async def explain_last(self): return {"explanation": "Running in standalone mode"}
        async def close(self): pass



class KalpanaShell:
    """
    The Kalpana Shell - AI-native command interface.
    
    Features:
    - Natural language commands (via Kalpana Core AI)
    - Traditional command fallback
    - Policy-aware execution
    - Explain mode
    """
    
    BANNER = """
    ┌─────────────────────────────────────────────────────┐
    │         🧠 KALPANA SHELL v0.1                       │
    │         AI-Native System Shell                      │
    │                                                     │
    │  Commands:                                          │
    │    .help     - Show help                            │
    │    .status   - System status                        │
    │    .explain  - Explain last decision                │
    │    .audit    - View audit log                       │
    │    .exit     - Exit shell                           │
    │                                                     │
    │  All commands are mediated by Kalpana Core.         │
    └─────────────────────────────────────────────────────┘
    """
    
    def __init__(self):
        self.client = KalpanaIPCClient(dev_mode=True)
        self.running = False
        self.cwd = os.getcwd()
        self.user = os.environ.get("USER", "unknown")
        self.hostname = os.uname().nodename
        self.history: list = []
        self.connected = False
    
    def get_prompt(self) -> str:
        """Generate shell prompt."""
        # Color codes
        CYAN = "\033[36m"
        GREEN = "\033[32m"
        YELLOW = "\033[33m"
        RESET = "\033[0m"
        
        status_icon = "🟢" if self.connected else "🔴"
        
        return f"{status_icon} {CYAN}{self.user}@{self.hostname}{RESET}:{GREEN}{self.cwd}{RESET}$ "
    
    async def connect_to_core(self):
        """Attempt to connect to Kalpana Core."""
        print("Connecting to Kalpana Core Authority...")
        self.connected = await self.client.connect()
        
        if self.connected:
            print("✅ Connected to Kalpana Core")
        else:
            print("⚠️  Running in STANDALONE mode (no policy enforcement)")
    
    async def execute_command(self, command: str) -> str:
        """Execute a command through Kalpana Core."""
        
        # Handle internal commands
        if command.startswith("."):
            return await self.handle_internal_command(command)
        
        # Handle cd specially
        if command.startswith("cd "):
            path = command[3:].strip()
            return self.change_directory(path)
        
        if command == "cd":
            return self.change_directory(os.path.expanduser("~"))
        
        # Request execution from Kalpana Core
        if self.connected:
            response = await self.client.execute(command)
            
            if not response.get("allowed", False):
                return f"❌ BLOCKED by Kalpana Core: {response.get('reason', 'Policy denied')}"
            
            # Log the approval
            decision = response.get("decision", "unknown")
            if decision == "audit":
                print(f"⚠️  Action logged for audit")
            elif decision == "sandbox":
                print(f"📦 Running in sandbox mode")
        
        # Execute the command
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                cwd=self.cwd
            )
            
            output = result.stdout
            if result.stderr:
                output += f"\n{result.stderr}"
            
            return output.strip() if output else ""
            
        except Exception as e:
            return f"❌ Execution error: {e}"
    
    async def handle_internal_command(self, command: str) -> str:
        """Handle shell internal commands."""
        cmd = command.lower().strip()
        
        if cmd == ".help":
            return self.BANNER
        
        elif cmd == ".status":
            if self.connected:
                status = await self.client.get_status()
                return (
                    f"🧠 Kalpana Core Status\n"
                    f"   Status: {status.get('status', 'unknown')}\n"
                    f"   Requests: {status.get('requests_processed', 0)}\n"
                    f"   Policies: {status.get('policies_loaded', 0)}\n"
                    f"   Mode: {status.get('mode', 'unknown')}"
                )
            else:
                return "⚠️  Not connected to Kalpana Core"
        
        elif cmd == ".explain":
            if self.connected:
                result = await self.client.explain_last()
                return result.get("explanation", "No explanation available")
            else:
                return "⚠️  Not connected to Kalpana Core"
        
        elif cmd == ".audit":
            if self.connected:
                result = await self.client.get_audit_log()
                entries = result.get("entries", [])
                if not entries:
                    return "No audit entries yet"
                
                output = "📋 Recent Audit Log:\n"
                for entry in entries[-10:]:
                    output += f"  - {entry}\n"
                return output
            else:
                return "⚠️  Not connected to Kalpana Core"
        
        elif cmd in [".exit", ".quit"]:
            self.running = False
            return "Goodbye! 👋"
        
        else:
            return f"Unknown command: {cmd}"
    
    def change_directory(self, path: str) -> str:
        """Change current directory."""
        try:
            # Expand ~ and resolve path
            path = os.path.expanduser(path)
            if not os.path.isabs(path):
                path = os.path.join(self.cwd, path)
            path = os.path.normpath(path)
            
            if os.path.isdir(path):
                self.cwd = path
                os.chdir(path)
                return ""
            else:
                return f"cd: no such directory: {path}"
        except Exception as e:
            return f"cd: {e}"
    
    async def run(self):
        """Main shell loop."""
        print(self.BANNER)
        
        # Connect to Kalpana Core
        await self.connect_to_core()
        
        self.running = True
        
        while self.running:
            try:
                # Get input
                command = input(self.get_prompt())
                command = command.strip()
                
                if not command:
                    continue
                
                # Add to history
                self.history.append(command)
                
                # Execute
                result = await self.execute_command(command)
                
                if result:
                    print(result)
                    
            except EOFError:
                print()
                break
            except KeyboardInterrupt:
                print("\n(Use .exit to quit)")
                continue
        
        # Cleanup
        await self.client.close()


async def main():
    shell = KalpanaShell()
    await shell.run()


if __name__ == "__main__":
    asyncio.run(main())
