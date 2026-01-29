#!/usr/bin/env python3
"""
Kalpana Web UI Server
=====================
Web-based alternative to GTK desktop.
Accessible via browser at http://localhost:7777
"""

import asyncio
import json
import os
import sys
from datetime import datetime
from typing import Dict, List

# Simple HTTP server
from http.server import HTTPServer, SimpleHTTPRequestHandler
import threading

# Path setup
UI_DIR = os.path.dirname(__file__)
STATIC_DIR = os.path.join(UI_DIR, 'static')

# Ensure static dir exists
os.makedirs(STATIC_DIR, exist_ok=True)


class KalpanaUIHandler(SimpleHTTPRequestHandler):
    """Custom HTTP handler for Kalpana UI."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=STATIC_DIR, **kwargs)
    
    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(get_html_content().encode())
        elif self.path == '/api/status':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(get_system_status()).encode())
        else:
            super().do_GET()
    
    def log_message(self, format, *args):
        pass  # Suppress logging


def get_system_status() -> Dict:
    """Get current system status."""
    try:
        import psutil
        return {
            "cpu": psutil.cpu_percent(),
            "memory": psutil.virtual_memory().percent,
            "disk": psutil.disk_usage('/').percent,
            "timestamp": datetime.now().isoformat()
        }
    except ImportError:
        return {
            "cpu": 0,
            "memory": 0,
            "disk": 0,
            "timestamp": datetime.now().isoformat()
        }


def get_html_content() -> str:
    """Generate the main HTML page."""
    return '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Kalpana OS - Desktop</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            background: linear-gradient(135deg, #0a0a0f 0%, #1a1a2e 100%);
            color: #fff;
            font-family: 'Courier New', monospace;
            min-height: 100vh;
        }
        
        .header {
            background: rgba(0, 0, 0, 0.5);
            border-bottom: 2px solid #00ffff;
            padding: 15px 30px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .logo {
            font-size: 24px;
            color: #00ffff;
            text-shadow: 0 0 10px #00ffff;
        }
        
        .status {
            color: #00ff00;
            font-size: 14px;
        }
        
        .status::before {
            content: '●';
            margin-right: 8px;
        }
        
        .main-content {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 20px;
            padding: 20px;
            max-width: 1400px;
            margin: 0 auto;
        }
        
        .panel {
            background: rgba(20, 20, 40, 0.8);
            border: 1px solid #00ffff;
            border-radius: 10px;
            padding: 20px;
            box-shadow: 0 0 20px rgba(0, 255, 255, 0.1);
        }
        
        .panel-title {
            color: #00ffff;
            font-size: 12px;
            letter-spacing: 3px;
            margin-bottom: 15px;
            text-transform: uppercase;
        }
        
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 15px;
        }
        
        .stat-item {
            text-align: center;
            padding: 15px;
            background: rgba(0, 255, 255, 0.05);
            border-radius: 8px;
        }
        
        .stat-value {
            font-size: 36px;
            font-weight: bold;
            color: #00ff00;
        }
        
        .stat-value.warning {
            color: #ffaa00;
        }
        
        .stat-value.critical {
            color: #ff0000;
        }
        
        .stat-label {
            font-size: 10px;
            color: #888;
            margin-top: 5px;
        }
        
        .alerts-list {
            max-height: 300px;
            overflow-y: auto;
        }
        
        .alert-item {
            background: rgba(255, 0, 0, 0.1);
            border-left: 3px solid #ff0000;
            padding: 10px 15px;
            margin-bottom: 8px;
            border-radius: 4px;
        }
        
        .alert-item.warning {
            background: rgba(255, 170, 0, 0.1);
            border-left-color: #ffaa00;
        }
        
        .alert-item.info {
            background: rgba(0, 255, 255, 0.1);
            border-left-color: #00ffff;
        }
        
        .alert-title {
            font-size: 13px;
            margin-bottom: 4px;
        }
        
        .alert-time {
            font-size: 10px;
            color: #666;
        }
        
        .device-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
            gap: 10px;
        }
        
        .device-item {
            background: rgba(0, 255, 255, 0.1);
            border: 1px solid #00ffff;
            border-radius: 6px;
            padding: 10px;
            text-align: center;
        }
        
        .device-ip {
            color: #00ffff;
            font-size: 12px;
            font-weight: bold;
        }
        
        .device-mac {
            font-size: 9px;
            color: #666;
        }
        
        .connection-list {
            font-size: 11px;
            color: #00ff00;
            max-height: 200px;
            overflow-y: auto;
        }
        
        .connection-item {
            padding: 5px 10px;
            border-bottom: 1px solid rgba(0, 255, 255, 0.1);
        }
        
        .toolbar {
            position: fixed;
            bottom: 0;
            left: 0;
            right: 0;
            background: rgba(0, 0, 0, 0.9);
            border-top: 1px solid #00ffff;
            padding: 15px 30px;
            display: flex;
            gap: 15px;
        }
        
        .toolbar-btn {
            background: transparent;
            border: 1px solid #00ffff;
            color: #00ffff;
            padding: 10px 20px;
            border-radius: 5px;
            cursor: pointer;
            font-family: inherit;
            transition: all 0.3s;
        }
        
        .toolbar-btn:hover {
            background: rgba(0, 255, 255, 0.2);
            box-shadow: 0 0 10px rgba(0, 255, 255, 0.3);
        }
        
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
        
        .pulse {
            animation: pulse 2s infinite;
        }
    </style>
</head>
<body>
    <header class="header">
        <div class="logo">🧠 KALPANA OS</div>
        <div class="status" id="status">ONLINE</div>
    </header>
    
    <main class="main-content">
        <div class="panel">
            <div class="panel-title">System Status</div>
            <div class="stats-grid">
                <div class="stat-item">
                    <div class="stat-value" id="cpu-value">--</div>
                    <div class="stat-label">CPU %</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value" id="mem-value">--</div>
                    <div class="stat-label">MEMORY %</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value" id="disk-value">--</div>
                    <div class="stat-label">DISK %</div>
                </div>
            </div>
        </div>
        
        <div class="panel">
            <div class="panel-title">Security Alerts</div>
            <div class="alerts-list" id="alerts-list">
                <div class="alert-item info">
                    <div class="alert-title">System Started</div>
                    <div class="alert-time">Just now</div>
                </div>
            </div>
        </div>
        
        <div class="panel">
            <div class="panel-title">Network Devices</div>
            <div class="device-grid" id="device-grid">
                <div class="device-item">
                    <div class="device-ip">Scanning...</div>
                    <div class="device-mac">Please wait</div>
                </div>
            </div>
        </div>
        
        <div class="panel">
            <div class="panel-title">Active Connections</div>
            <div class="connection-list" id="connection-list">
                <div class="connection-item">Loading...</div>
            </div>
        </div>
    </main>
    
    <footer class="toolbar">
        <button class="toolbar-btn">🖥️ Shell</button>
        <button class="toolbar-btn">🔒 Security</button>
        <button class="toolbar-btn">🌐 Network</button>
        <button class="toolbar-btn">📋 Logs</button>
        <button class="toolbar-btn">⚙️ Settings</button>
    </footer>
    
    <script>
        async function updateStatus() {
            try {
                const response = await fetch('/api/status');
                const data = await response.json();
                
                // Update CPU
                const cpuEl = document.getElementById('cpu-value');
                cpuEl.textContent = Math.round(data.cpu);
                cpuEl.className = 'stat-value';
                if (data.cpu >= 80) cpuEl.classList.add('critical');
                else if (data.cpu >= 50) cpuEl.classList.add('warning');
                
                // Update Memory
                const memEl = document.getElementById('mem-value');
                memEl.textContent = Math.round(data.memory);
                memEl.className = 'stat-value';
                if (data.memory >= 80) memEl.classList.add('critical');
                else if (data.memory >= 50) memEl.classList.add('warning');
                
                // Update Disk
                const diskEl = document.getElementById('disk-value');
                diskEl.textContent = Math.round(data.disk);
                diskEl.className = 'stat-value';
                if (data.disk >= 90) diskEl.classList.add('critical');
                else if (data.disk >= 70) diskEl.classList.add('warning');
                
            } catch (error) {
                console.error('Status update failed:', error);
            }
        }
        
        // Update every 2 seconds
        setInterval(updateStatus, 2000);
        updateStatus();
    </script>
</body>
</html>
'''


def run_server(port: int = 7777):
    """Run the web UI server."""
    print(f"""
    ╔═══════════════════════════════════════════════════════════╗
    ║                                                           ║
    ║    🌐 KALPANA WEB UI                                       ║
    ║                                                           ║
    ║    Open browser: http://localhost:{port}                    ║
    ║                                                           ║
    ╚═══════════════════════════════════════════════════════════╝
    """)
    
    server = HTTPServer(('0.0.0.0', port), KalpanaUIHandler)
    print(f"Server running on http://localhost:{port}")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down...")
        server.shutdown()


if __name__ == "__main__":
    run_server()
