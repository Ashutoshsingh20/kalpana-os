#!/usr/bin/env python3
"""
Kalpana Session Manager
=======================
Manages user sessions, login, and desktop startup.
"""

import asyncio
import json
import os
import sys
import subprocess
from datetime import datetime
from typing import Optional, Dict
from pathlib import Path

# Session storage
SESSION_DIR = Path("/tmp/kalpana-sessions")
SESSION_DIR.mkdir(parents=True, exist_ok=True)


class Session:
    """User session."""
    
    def __init__(self, user: str):
        self.user = user
        self.started_at = datetime.now()
        self.pid = os.getpid()
        self.display = os.environ.get("DISPLAY", ":0")
        self.wayland_display = os.environ.get("WAYLAND_DISPLAY", "")
    
    def to_dict(self) -> Dict:
        return {
            "user": self.user,
            "started_at": self.started_at.isoformat(),
            "pid": self.pid,
            "display": self.display,
            "wayland_display": self.wayland_display
        }
    
    def save(self):
        """Save session to file."""
        path = SESSION_DIR / f"{self.user}.json"
        path.write_text(json.dumps(self.to_dict(), indent=2))
    
    @staticmethod
    def load(user: str) -> Optional['Session']:
        """Load existing session."""
        path = SESSION_DIR / f"{user}.json"
        if path.exists():
            data = json.loads(path.read_text())
            session = Session(data["user"])
            session.started_at = datetime.fromisoformat(data["started_at"])
            session.pid = data["pid"]
            return session
        return None


class SessionManager:
    """Manages user sessions and desktop startup."""
    
    def __init__(self):
        self.current_session: Optional[Session] = None
    
    def login(self, user: str, password: str = "") -> bool:
        """
        Login a user.
        In production, this would verify credentials via PAM.
        """
        print(f"🔐 Authenticating user: {user}")
        
        # Create session
        self.current_session = Session(user)
        self.current_session.save()
        
        print(f"✅ User {user} logged in successfully")
        return True
    
    def logout(self):
        """Logout current user."""
        if self.current_session:
            user = self.current_session.user
            path = SESSION_DIR / f"{user}.json"
            if path.exists():
                path.unlink()
            print(f"👋 User {user} logged out")
            self.current_session = None
    
    def start_desktop(self, use_web: bool = False):
        """Start the desktop environment."""
        if not self.current_session:
            print("❌ No active session")
            return
        
        print(f"🖥️ Starting desktop for {self.current_session.user}...")
        
        if use_web:
            # Start web UI
            subprocess.Popen([
                sys.executable,
                os.path.join(os.path.dirname(__file__), "webui.py")
            ])
            print("🌐 Web UI started at http://localhost:7777")
        else:
            # Start GTK desktop
            subprocess.Popen([
                sys.executable,
                os.path.join(os.path.dirname(__file__), "desktop.py")
            ])
            print("🖥️ GTK Desktop started")
    
    def get_active_sessions(self) -> list:
        """Get all active sessions."""
        sessions = []
        for path in SESSION_DIR.glob("*.json"):
            try:
                data = json.loads(path.read_text())
                sessions.append(data)
            except:
                pass
        return sessions


def main():
    print("""
    ╔═══════════════════════════════════════════════════════════╗
    ║                                                           ║
    ║    🔐 KALPANA SESSION MANAGER                              ║
    ║                                                           ║
    ╚═══════════════════════════════════════════════════════════╝
    """)
    
    manager = SessionManager()
    
    # Auto-login for development
    user = os.environ.get("USER", "kalpana")
    manager.login(user)
    
    # Start desktop (web UI by default for cross-platform)
    manager.start_desktop(use_web=True)
    
    print("\nSession active. Press Ctrl+C to logout.")
    
    try:
        while True:
            asyncio.run(asyncio.sleep(1))
    except KeyboardInterrupt:
        manager.logout()


if __name__ == "__main__":
    main()
