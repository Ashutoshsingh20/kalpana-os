#!/usr/bin/env python3
"""
Kalpana Security - Main Entry Point
====================================
Combines Network Monitor, IDS, and Firewall into unified security stack.
"""

import asyncio
import logging
import os
import signal
import sys
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.dirname(__file__))

from network import NetworkMonitor, ThreatLevel
from ids import IntrusionDetectionSystem

class KalpanaSecurityDaemon:
    """
    Unified security daemon for Kalpana OS.
    Integrates all security components.
    """
    
    def __init__(self):
        self.network_monitor = NetworkMonitor()
        self.ids = IntrusionDetectionSystem()
        self.running = False
        
        # Register IDS with network monitor
        self.network_monitor.alert_callbacks.append(self._on_network_alert)
        
        logging.info("🛡️ Kalpana Security Daemon initialized")
    
    async def _on_network_alert(self, alert):
        """Handle network alerts - cross-correlate with IDS."""
        logging.debug(f"Network alert received: {alert.title}")
    
    async def start(self):
        """Start the security daemon."""
        self.running = True
        
        # Setup signal handlers
        signal.signal(signal.SIGTERM, self._handle_shutdown)
        signal.signal(signal.SIGINT, self._handle_shutdown)
        
        logging.info("🚀 Starting Kalpana Security Daemon...")
        
        # Start components
        await self.network_monitor.start()
    
    def _handle_shutdown(self, signum, frame):
        """Handle shutdown signal."""
        logging.info("⚠️ Shutting down security daemon...")
        self.running = False
    
    async def stop(self):
        """Stop the security daemon."""
        await self.network_monitor.stop()
        logging.info("👋 Security daemon stopped")
    
    def get_full_status(self) -> dict:
        """Get combined security status."""
        return {
            "network": self.network_monitor.get_status(),
            "ids": self.ids.get_statistics(),
            "timestamp": datetime.now().isoformat()
        }


async def main():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s | %(levelname)s | %(message)s'
    )
    
    print("""
    ╔═══════════════════════════════════════════════════════════╗
    ║                                                           ║
    ║    🛡️  KALPANA SECURITY DAEMON                            ║
    ║                                                           ║
    ║    Unified Network Security & Intrusion Detection         ║
    ║                                                           ║
    ║    Components:                                            ║
    ║      • Network Monitor                                    ║
    ║      • Firewall Manager                                   ║
    ║      • Intrusion Detection System                         ║
    ║      • Threat Detector                                    ║
    ║                                                           ║
    ╚═══════════════════════════════════════════════════════════╝
    """)
    
    daemon = KalpanaSecurityDaemon()
    
    try:
        await daemon.start()
    except KeyboardInterrupt:
        pass
    finally:
        await daemon.stop()


if __name__ == "__main__":
    asyncio.run(main())
