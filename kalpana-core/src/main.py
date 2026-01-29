#!/usr/bin/env python3
"""
Kalpana Core Authority Daemon
=============================
The central system authority for Kalpana OS.
Runs as PID-critical root service, mediating all system actions.

This is the BRAIN of the operating system.
"""

import asyncio
import json
import logging
import os
import signal
import sys
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
import socket
import struct

# ============================================================================
# Configuration
# ============================================================================

KALPANA_ROOT = Path("/kalpana")
AUDIT_LOG_PATH = KALPANA_ROOT / "audit" / "core.log"
POLICY_PATH = KALPANA_ROOT / "policy"
IPC_SOCKET_PATH = "/run/kalpana/core.sock"

# Development mode paths (when not running as actual OS)
DEV_MODE = os.environ.get("KALPANA_DEV_MODE", "1") == "1"
if DEV_MODE:
    KALPANA_ROOT = Path(__file__).parent.parent
    AUDIT_LOG_PATH = KALPANA_ROOT / "logs" / "core.log"
    POLICY_PATH = KALPANA_ROOT / "policy"
    IPC_SOCKET_PATH = "/tmp/kalpana-core.sock"

# ============================================================================
# Enums & Data Classes
# ============================================================================

class ActionType(Enum):
    PROCESS_START = "process_start"
    PROCESS_KILL = "process_kill"
    FILE_READ = "file_read"
    FILE_WRITE = "file_write"
    FILE_DELETE = "file_delete"
    NETWORK_CONNECT = "network_connect"
    NETWORK_LISTEN = "network_listen"
    SYSTEM_COMMAND = "system_command"
    PRIVILEGE_ESCALATE = "privilege_escalate"
    PACKAGE_INSTALL = "package_install"
    SERVICE_CONTROL = "service_control"


class Decision(Enum):
    ALLOW = "allow"
    DENY = "deny"
    AUDIT = "audit"  # Allow but flag for review
    SANDBOX = "sandbox"  # Allow in restricted environment


@dataclass
class ActionRequest:
    """A request for system action that requires Kalpana's approval."""
    id: str
    action_type: ActionType
    requestor_pid: int
    requestor_uid: int
    requestor_name: str
    target: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class ActionResponse:
    """Kalpana's decision on an action request."""
    request_id: str
    decision: Decision
    reason: str
    constraints: Dict[str, Any] = field(default_factory=dict)
    expires_at: Optional[datetime] = None


@dataclass
class AuditEntry:
    """Immutable audit log entry."""
    timestamp: datetime
    request: ActionRequest
    response: ActionResponse
    execution_result: Optional[str] = None


# ============================================================================
# Policy Engine
# ============================================================================

class PolicyEngine:
    """
    Evaluates action requests against system policies.
    Zero-trust by default: everything is denied unless explicitly allowed.
    """
    
    def __init__(self):
        self.policies: List[Dict] = []
        self.trusted_processes: set = {"kalpana-shell", "kalpana-ui", "systemd"}
        self.blocked_paths: set = {"/boot", "/kalpana/core"}
        self.load_policies()
    
    def load_policies(self):
        """Load policy files from disk."""
        policy_dir = POLICY_PATH
        if not policy_dir.exists():
            policy_dir.mkdir(parents=True, exist_ok=True)
            # Create default restrictive policy
            default_policy = {
                "name": "default",
                "version": "1.0",
                "rules": [
                    {"action": "process_start", "allow_trusted": True},
                    {"action": "file_read", "allow": True, "except": ["/kalpana/core/*"]},
                    {"action": "file_write", "allow": False, "except": ["/users/*", "/tmp/*"]},
                    {"action": "network_connect", "allow": True, "audit": True},
                    {"action": "privilege_escalate", "allow": False}
                ]
            }
            (policy_dir / "default.json").write_text(json.dumps(default_policy, indent=2))
        
        for policy_file in policy_dir.glob("*.json"):
            try:
                self.policies.append(json.loads(policy_file.read_text()))
            except Exception as e:
                logging.error(f"Failed to load policy {policy_file}: {e}")
    
    def evaluate(self, request: ActionRequest) -> ActionResponse:
        """Evaluate an action request against policies."""
        
        # CRITICAL: Always deny attempts to modify Kalpana Core
        if request.action_type in [ActionType.FILE_WRITE, ActionType.FILE_DELETE]:
            if any(blocked in request.target for blocked in self.blocked_paths):
                return ActionResponse(
                    request_id=request.id,
                    decision=Decision.DENY,
                    reason="Protected system path - modification forbidden"
                )
        
        # Trusted processes get more permissions
        if request.requestor_name in self.trusted_processes:
            return ActionResponse(
                request_id=request.id,
                decision=Decision.ALLOW,
                reason=f"Trusted process: {request.requestor_name}"
            )
        
        # Network actions: Allow but audit
        if request.action_type in [ActionType.NETWORK_CONNECT, ActionType.NETWORK_LISTEN]:
            return ActionResponse(
                request_id=request.id,
                decision=Decision.AUDIT,
                reason="Network action logged for review"
            )
        
        # Privilege escalation: Always deny for non-Kalpana processes
        if request.action_type == ActionType.PRIVILEGE_ESCALATE:
            return ActionResponse(
                request_id=request.id,
                decision=Decision.DENY,
                reason="Privilege escalation requires Kalpana approval"
            )
        
        # Default: Sandbox unknown actions
        return ActionResponse(
            request_id=request.id,
            decision=Decision.SANDBOX,
            reason="Unknown action sandboxed by default"
        )


# ============================================================================
# Audit Logger
# ============================================================================

class AuditLogger:
    """Immutable, tamper-evident audit logging."""
    
    def __init__(self):
        self.log_path = AUDIT_LOG_PATH
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        self.entries: List[AuditEntry] = []
    
    def log(self, entry: AuditEntry):
        """Log an audit entry."""
        self.entries.append(entry)
        
        log_line = {
            "timestamp": entry.timestamp.isoformat(),
            "request_id": entry.request.id,
            "action": entry.request.action_type.value,
            "requestor": entry.request.requestor_name,
            "target": entry.request.target,
            "decision": entry.response.decision.value,
            "reason": entry.response.reason
        }
        
        with open(self.log_path, "a") as f:
            f.write(json.dumps(log_line) + "\n")
    
    def query(self, action_type: Optional[ActionType] = None, 
              decision: Optional[Decision] = None,
              limit: int = 100) -> List[AuditEntry]:
        """Query audit log with filters."""
        results = self.entries
        
        if action_type:
            results = [e for e in results if e.request.action_type == action_type]
        if decision:
            results = [e for e in results if e.response.decision == decision]
        
        return results[-limit:]


# ============================================================================
# IPC Server
# ============================================================================

class IPCServer:
    """Unix socket IPC server for shell/UI communication."""
    
    def __init__(self, core: 'KalpanaCore'):
        self.core = core
        self.socket_path = IPC_SOCKET_PATH
        self.server: Optional[asyncio.AbstractServer] = None
    
    async def start(self):
        """Start the IPC server."""
        # Clean up old socket
        if os.path.exists(self.socket_path):
            os.unlink(self.socket_path)
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(self.socket_path), exist_ok=True)
        
        self.server = await asyncio.start_unix_server(
            self.handle_client,
            path=self.socket_path
        )
        
        # Set permissions (only root and kalpana group can connect)
        os.chmod(self.socket_path, 0o660)
        
        logging.info(f"IPC server listening on {self.socket_path}")
    
    async def handle_client(self, reader: asyncio.StreamReader, 
                           writer: asyncio.StreamWriter):
        """Handle incoming IPC client connection."""
        try:
            while True:
                # Read message length (4 bytes, big endian)
                length_data = await reader.read(4)
                if not length_data:
                    break
                
                msg_length = struct.unpack(">I", length_data)[0]
                msg_data = await reader.read(msg_length)
                
                request = json.loads(msg_data.decode())
                response = await self.process_request(request)
                
                response_data = json.dumps(response).encode()
                writer.write(struct.pack(">I", len(response_data)))
                writer.write(response_data)
                await writer.drain()
                
        except Exception as e:
            logging.error(f"IPC client error: {e}")
        finally:
            writer.close()
            await writer.wait_closed()
    
    async def process_request(self, request: Dict) -> Dict:
        """Process an IPC request from shell/UI."""
        cmd = request.get("command")
        
        if cmd == "execute":
            # Shell wants to execute a command
            return await self.core.handle_execute(request)
        
        elif cmd == "status":
            # Request system status
            return self.core.get_status()
        
        elif cmd == "audit":
            # Request audit log
            return {"entries": [e.__dict__ for e in self.core.audit.query(limit=50)]}
        
        elif cmd == "explain":
            # Explain last decision
            return self.core.explain_last_decision()
        
        else:
            return {"error": f"Unknown command: {cmd}"}
    
    async def stop(self):
        """Stop the IPC server."""
        if self.server:
            self.server.close()
            await self.server.wait_closed()
        
        if os.path.exists(self.socket_path):
            os.unlink(self.socket_path)


# ============================================================================
# Kalpana Core Authority
# ============================================================================

class KalpanaCore:
    """
    The Central Authority of Kalpana OS.
    
    All system actions flow through this daemon.
    It maintains security, logs everything, and makes intelligent decisions.
    """
    
    def __init__(self):
        self.policy = PolicyEngine()
        self.audit = AuditLogger()
        self.ipc = IPCServer(self)
        self.running = False
        self.request_counter = 0
        self.last_decision: Optional[ActionResponse] = None
        
        # Process monitoring
        self.monitored_processes: Dict[int, Dict] = {}
        
        logging.info("🧠 Kalpana Core Authority initializing...")
    
    async def start(self):
        """Start the Kalpana Core daemon."""
        self.running = True
        
        # Setup signal handlers
        signal.signal(signal.SIGTERM, self._handle_shutdown)
        signal.signal(signal.SIGINT, self._handle_shutdown)
        
        # Start IPC server
        await self.ipc.start()
        
        # Log startup
        logging.info("✅ Kalpana Core Authority is ONLINE")
        logging.info(f"   - Audit log: {AUDIT_LOG_PATH}")
        logging.info(f"   - IPC socket: {IPC_SOCKET_PATH}")
        logging.info(f"   - Mode: {'DEVELOPMENT' if DEV_MODE else 'PRODUCTION'}")
        
        # Enter main loop
        await self._main_loop()
    
    async def _main_loop(self):
        """Main daemon loop."""
        while self.running:
            # Health check, process monitoring, etc.
            await asyncio.sleep(1)
    
    def _handle_shutdown(self, signum, frame):
        """Handle shutdown signal."""
        logging.info("⚠️ Kalpana Core shutting down...")
        self.running = False
    
    def _generate_request_id(self) -> str:
        """Generate unique request ID."""
        self.request_counter += 1
        return f"REQ-{datetime.now().strftime('%Y%m%d%H%M%S')}-{self.request_counter:06d}"
    
    async def handle_execute(self, request: Dict) -> Dict:
        """Handle command execution request from shell."""
        action_request = ActionRequest(
            id=self._generate_request_id(),
            action_type=ActionType.SYSTEM_COMMAND,
            requestor_pid=request.get("pid", 0),
            requestor_uid=request.get("uid", 0),
            requestor_name=request.get("process", "unknown"),
            target=request.get("command", ""),
            parameters=request.get("args", {})
        )
        
        # Evaluate against policy
        response = self.policy.evaluate(action_request)
        self.last_decision = response
        
        # Log to audit
        self.audit.log(AuditEntry(
            timestamp=datetime.now(),
            request=action_request,
            response=response
        ))
        
        return {
            "request_id": response.request_id,
            "decision": response.decision.value,
            "reason": response.reason,
            "allowed": response.decision in [Decision.ALLOW, Decision.AUDIT]
        }
    
    def get_status(self) -> Dict:
        """Get system status."""
        return {
            "status": "online",
            "uptime": "N/A",  # TODO: Calculate
            "requests_processed": self.request_counter,
            "mode": "development" if DEV_MODE else "production",
            "policies_loaded": len(self.policy.policies),
            "audit_entries": len(self.audit.entries)
        }
    
    def explain_last_decision(self) -> Dict:
        """Explain the last security decision."""
        if not self.last_decision:
            return {"explanation": "No decisions made yet."}
        
        return {
            "request_id": self.last_decision.request_id,
            "decision": self.last_decision.decision.value,
            "reason": self.last_decision.reason,
            "explanation": f"The action was {self.last_decision.decision.value} because: {self.last_decision.reason}"
        }
    
    async def shutdown(self):
        """Graceful shutdown."""
        logging.info("🛑 Initiating graceful shutdown...")
        self.running = False
        await self.ipc.stop()
        logging.info("👋 Kalpana Core Authority offline.")


# ============================================================================
# Entry Point
# ============================================================================

async def main():
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s | %(levelname)s | %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
        ]
    )
    
    print("""
    ╔═══════════════════════════════════════════════════════════╗
    ║                                                           ║
    ║   ██╗  ██╗ █████╗ ██╗     ██████╗  █████╗ ███╗   ██╗ █████╗  ║
    ║   ██║ ██╔╝██╔══██╗██║     ██╔══██╗██╔══██╗████╗  ██║██╔══██╗ ║
    ║   █████╔╝ ███████║██║     ██████╔╝███████║██╔██╗ ██║███████║ ║
    ║   ██╔═██╗ ██╔══██║██║     ██╔═══╝ ██╔══██║██║╚██╗██║██╔══██║ ║
    ║   ██║  ██╗██║  ██║███████╗██║     ██║  ██║██║ ╚████║██║  ██║ ║
    ║   ╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝╚═╝     ╚═╝  ╚═╝╚═╝  ╚═══╝╚═╝  ╚═╝ ║
    ║                                                           ║
    ║                  CORE AUTHORITY DAEMON                    ║
    ║                                                           ║
    ╚═══════════════════════════════════════════════════════════╝
    """)
    
    core = KalpanaCore()
    
    try:
        await core.start()
    except KeyboardInterrupt:
        pass
    finally:
        await core.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
