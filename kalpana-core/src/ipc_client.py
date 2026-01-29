#!/usr/bin/env python3
"""
Kalpana IPC Client Library
==========================
Used by kalpana-shell and kalpana-ui to communicate with kalpana-core.
"""

import asyncio
import json
import os
import socket
import struct
from typing import Dict, Any, Optional

IPC_SOCKET_PATH = "/run/kalpana/core.sock"
DEV_SOCKET_PATH = "/tmp/kalpana-core.sock"


class KalpanaIPCClient:
    """Client for communicating with Kalpana Core Authority."""
    
    def __init__(self, dev_mode: bool = True):
        self.socket_path = DEV_SOCKET_PATH if dev_mode else IPC_SOCKET_PATH
        self.reader: Optional[asyncio.StreamReader] = None
        self.writer: Optional[asyncio.StreamWriter] = None
        self.connected = False
    
    async def connect(self) -> bool:
        """Connect to Kalpana Core."""
        try:
            self.reader, self.writer = await asyncio.open_unix_connection(
                path=self.socket_path
            )
            self.connected = True
            return True
        except Exception as e:
            print(f"❌ Failed to connect to Kalpana Core: {e}")
            return False
    
    async def send_request(self, request: Dict) -> Dict:
        """Send a request and wait for response."""
        if not self.connected:
            if not await self.connect():
                return {"error": "Not connected to Kalpana Core"}
        
        try:
            # Encode and send
            data = json.dumps(request).encode()
            self.writer.write(struct.pack(">I", len(data)))
            self.writer.write(data)
            await self.writer.drain()
            
            # Read response
            length_data = await self.reader.read(4)
            if not length_data:
                return {"error": "Connection closed"}
            
            msg_length = struct.unpack(">I", length_data)[0]
            response_data = await self.reader.read(msg_length)
            
            return json.loads(response_data.decode())
            
        except Exception as e:
            return {"error": str(e)}
    
    async def execute(self, command: str, args: Dict = None) -> Dict:
        """Request command execution from Kalpana Core."""
        return await self.send_request({
            "command": "execute",
            "cmd": command,
            "args": args or {},
            "pid": os.getpid(),
            "uid": os.getuid(),
            "process": "kalpana-shell"
        })
    
    async def get_status(self) -> Dict:
        """Get system status from Kalpana Core."""
        return await self.send_request({"command": "status"})
    
    async def get_audit_log(self, limit: int = 50) -> Dict:
        """Get recent audit log entries."""
        return await self.send_request({"command": "audit", "limit": limit})
    
    async def explain_last(self) -> Dict:
        """Get explanation of last security decision."""
        return await self.send_request({"command": "explain"})
    
    async def close(self):
        """Close the connection."""
        if self.writer:
            self.writer.close()
            await self.writer.wait_closed()
        self.connected = False


# Convenience functions for synchronous usage
def sync_execute(command: str) -> Dict:
    """Synchronous wrapper for execute."""
    async def _run():
        client = KalpanaIPCClient()
        result = await client.execute(command)
        await client.close()
        return result
    return asyncio.run(_run())


def sync_status() -> Dict:
    """Synchronous wrapper for status."""
    async def _run():
        client = KalpanaIPCClient()
        result = await client.get_status()
        await client.close()
        return result
    return asyncio.run(_run())


if __name__ == "__main__":
    # Quick test
    async def test():
        client = KalpanaIPCClient()
        
        print("Connecting to Kalpana Core...")
        if await client.connect():
            print("✅ Connected!")
            
            print("\nSystem Status:")
            status = await client.get_status()
            print(json.dumps(status, indent=2))
            
            print("\nTesting command execution:")
            result = await client.execute("ls -la")
            print(json.dumps(result, indent=2))
            
            await client.close()
        else:
            print("❌ Could not connect. Is kalpana-core running?")
    
    asyncio.run(test())
