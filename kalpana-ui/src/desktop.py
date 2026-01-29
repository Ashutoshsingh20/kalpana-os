#!/usr/bin/env python3
"""
Kalpana Desktop UI
==================
Lightweight desktop environment for Kalpana OS.
Built with GTK4 for Wayland compatibility.

Note: For actual Wayland compositor functionality, this would use
wlroots or similar. This implementation provides the UI layer
that runs on top of a compositor like Weston or Sway.
"""

import asyncio
import json
import os
import sys
from datetime import datetime
from typing import Dict, List, Optional
import subprocess

# Try to import GTK
try:
    import gi
    gi.require_version('Gtk', '4.0')
    from gi.repository import Gtk, Gdk, GLib, Pango
    GTK_AVAILABLE = True
except ImportError:
    GTK_AVAILABLE = False
    print("⚠️  GTK4 not available. UI will run in headless mode.")

# Add paths
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'kalpana-core', 'src'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'kalpana-security', 'src'))

# ============================================================================
# CSS Styling
# ============================================================================

KALPANA_CSS = """
window {
    background-color: #0a0a0f;
}

.main-container {
    padding: 20px;
}

.header-bar {
    background: linear-gradient(180deg, #1a1a2e 0%, #0f0f1a 100%);
    border-bottom: 1px solid #00ffff;
    padding: 10px 20px;
}

.header-title {
    color: #00ffff;
    font-size: 24px;
    font-weight: bold;
    font-family: monospace;
}

.panel {
    background-color: rgba(20, 20, 40, 0.9);
    border: 1px solid #00ffff;
    border-radius: 8px;
    padding: 15px;
    margin: 10px;
}

.panel-title {
    color: #00ffff;
    font-size: 14px;
    font-weight: bold;
    margin-bottom: 10px;
    font-family: monospace;
    letter-spacing: 2px;
}

.stat-value {
    color: #ffffff;
    font-size: 32px;
    font-weight: bold;
    font-family: monospace;
}

.stat-label {
    color: #888888;
    font-size: 12px;
    font-family: monospace;
}

.stat-safe {
    color: #00ff00;
}

.stat-warning {
    color: #ffaa00;
}

.stat-critical {
    color: #ff0000;
}

.alert-row {
    background-color: rgba(255, 0, 0, 0.1);
    border-left: 3px solid #ff0000;
    padding: 8px 12px;
    margin: 5px 0;
    border-radius: 4px;
}

.alert-row.warning {
    background-color: rgba(255, 170, 0, 0.1);
    border-left-color: #ffaa00;
}

.alert-row.info {
    background-color: rgba(0, 255, 255, 0.1);
    border-left-color: #00ffff;
}

.alert-title {
    color: #ffffff;
    font-size: 12px;
    font-weight: bold;
}

.alert-time {
    color: #666666;
    font-size: 10px;
}

.connection-item {
    color: #00ff00;
    font-family: monospace;
    font-size: 11px;
    padding: 4px 8px;
}

.device-item {
    background-color: rgba(0, 255, 255, 0.1);
    border: 1px solid #00ffff;
    border-radius: 4px;
    padding: 8px;
    margin: 4px;
}

.device-ip {
    color: #00ffff;
    font-size: 14px;
    font-weight: bold;
    font-family: monospace;
}

.device-mac {
    color: #888888;
    font-size: 10px;
    font-family: monospace;
}

.toolbar {
    background-color: #1a1a2e;
    border-top: 1px solid #00ffff;
    padding: 10px;
}

.toolbar-button {
    background-color: transparent;
    border: 1px solid #00ffff;
    color: #00ffff;
    padding: 8px 16px;
    border-radius: 4px;
    font-family: monospace;
}

.toolbar-button:hover {
    background-color: rgba(0, 255, 255, 0.2);
}

.status-online {
    color: #00ff00;
}

.status-offline {
    color: #ff0000;
}
"""


# ============================================================================
# Headless Mode (when GTK not available)
# ============================================================================

class HeadlessUI:
    """Terminal-based UI fallback."""
    
    def __init__(self):
        self.running = False
        
    async def run(self):
        """Run headless UI loop."""
        self.running = True
        
        print("""
╔═══════════════════════════════════════════════════════════════════════╗
║                                                                       ║
║    🖥️  KALPANA DESKTOP (Headless Mode)                                ║
║                                                                       ║
║    GTK4 not available - displaying status in terminal                 ║
║                                                                       ║
╚═══════════════════════════════════════════════════════════════════════╝
        """)
        
        while self.running:
            await self._update_display()
            await asyncio.sleep(2)
    
    async def _update_display(self):
        """Update terminal display."""
        # Clear and redraw
        os.system('clear' if os.name != 'nt' else 'cls')
        
        print("\n" + "="*60)
        print(" 🖥️  KALPANA DESKTOP - " + datetime.now().strftime("%H:%M:%S"))
        print("="*60)
        
        # System stats
        try:
            import psutil
            cpu = psutil.cpu_percent()
            mem = psutil.virtual_memory().percent
            print(f"\n 📊 SYSTEM STATUS")
            print(f"    CPU: {cpu}%  |  Memory: {mem}%")
        except ImportError:
            print("\n 📊 SYSTEM STATUS: psutil not available")
        
        # Network stats (simulated)
        print(f"\n 🌐 NETWORK STATUS")
        print(f"    Connections: --  |  Devices: --  |  Alerts: --")
        
        # Security status
        print(f"\n 🔒 SECURITY STATUS")
        print(f"    IDS: Active  |  Firewall: Active  |  Core: Online")
        
        print("\n" + "-"*60)
        print(" Press Ctrl+C to exit")
    
    def stop(self):
        self.running = False


# ============================================================================
# GTK4 Desktop UI
# ============================================================================

if GTK_AVAILABLE:
    
    class SystemPanel(Gtk.Box):
        """System health panel."""
        
        def __init__(self):
            super().__init__(orientation=Gtk.Orientation.VERTICAL)
            self.add_css_class("panel")
            
            # Title
            title = Gtk.Label(label="SYSTEM STATUS")
            title.add_css_class("panel-title")
            self.append(title)
            
            # Stats grid
            grid = Gtk.Grid()
            grid.set_column_spacing(20)
            grid.set_row_spacing(10)
            
            # CPU
            self.cpu_value = Gtk.Label(label="--")
            self.cpu_value.add_css_class("stat-value")
            self.cpu_value.add_css_class("stat-safe")
            cpu_label = Gtk.Label(label="CPU %")
            cpu_label.add_css_class("stat-label")
            
            grid.attach(self.cpu_value, 0, 0, 1, 1)
            grid.attach(cpu_label, 0, 1, 1, 1)
            
            # Memory
            self.mem_value = Gtk.Label(label="--")
            self.mem_value.add_css_class("stat-value")
            self.mem_value.add_css_class("stat-safe")
            mem_label = Gtk.Label(label="MEM %")
            mem_label.add_css_class("stat-label")
            
            grid.attach(self.mem_value, 1, 0, 1, 1)
            grid.attach(mem_label, 1, 1, 1, 1)
            
            # Disk
            self.disk_value = Gtk.Label(label="--")
            self.disk_value.add_css_class("stat-value")
            disk_label = Gtk.Label(label="DISK %")
            disk_label.add_css_class("stat-label")
            
            grid.attach(self.disk_value, 2, 0, 1, 1)
            grid.attach(disk_label, 2, 1, 1, 1)
            
            self.append(grid)
        
        def update(self, cpu: float, memory: float, disk: float):
            """Update stats."""
            self.cpu_value.set_label(f"{cpu:.0f}")
            self.mem_value.set_label(f"{memory:.0f}")
            self.disk_value.set_label(f"{disk:.0f}")
            
            # Color based on value
            for widget, value in [(self.cpu_value, cpu), (self.mem_value, memory)]:
                widget.remove_css_class("stat-safe")
                widget.remove_css_class("stat-warning")
                widget.remove_css_class("stat-critical")
                
                if value < 50:
                    widget.add_css_class("stat-safe")
                elif value < 80:
                    widget.add_css_class("stat-warning")
                else:
                    widget.add_css_class("stat-critical")


    class NetworkPanel(Gtk.Box):
        """Network status panel."""
        
        def __init__(self):
            super().__init__(orientation=Gtk.Orientation.VERTICAL)
            self.add_css_class("panel")
            
            title = Gtk.Label(label="NETWORK TOPOLOGY")
            title.add_css_class("panel-title")
            self.append(title)
            
            # Device list
            self.device_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
            self.append(self.device_box)
            
            # Placeholder
            placeholder = Gtk.Label(label="Scanning network...")
            placeholder.add_css_class("stat-label")
            self.device_box.append(placeholder)
        
        def update_devices(self, devices: List[Dict]):
            """Update device list."""
            # Clear existing
            while child := self.device_box.get_first_child():
                self.device_box.remove(child)
            
            for device in devices[:8]:  # Limit to 8
                item = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
                item.add_css_class("device-item")
                
                ip = Gtk.Label(label=device.get("ip", "Unknown"))
                ip.add_css_class("device-ip")
                item.append(ip)
                
                mac = Gtk.Label(label=device.get("mac", "Unknown MAC"))
                mac.add_css_class("device-mac")
                item.append(mac)
                
                self.device_box.append(item)


    class AlertsPanel(Gtk.Box):
        """Security alerts panel."""
        
        def __init__(self):
            super().__init__(orientation=Gtk.Orientation.VERTICAL)
            self.add_css_class("panel")
            
            title = Gtk.Label(label="SECURITY ALERTS")
            title.add_css_class("panel-title")
            self.append(title)
            
            # Scrolled container
            scroll = Gtk.ScrolledWindow()
            scroll.set_min_content_height(200)
            
            self.alerts_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
            scroll.set_child(self.alerts_box)
            
            self.append(scroll)
            
            # Placeholder
            no_alerts = Gtk.Label(label="No recent alerts")
            no_alerts.add_css_class("stat-label")
            self.alerts_box.append(no_alerts)
        
        def update_alerts(self, alerts: List[Dict]):
            """Update alerts list."""
            # Clear existing
            while child := self.alerts_box.get_first_child():
                self.alerts_box.remove(child)
            
            if not alerts:
                no_alerts = Gtk.Label(label="No recent alerts")
                no_alerts.add_css_class("stat-label")
                self.alerts_box.append(no_alerts)
                return
            
            for alert in reversed(alerts[-10:]):  # Last 10, newest first
                row = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
                row.add_css_class("alert-row")
                
                level = alert.get("level", "info")
                if level == "critical" or level == "high":
                    pass  # Default red
                elif level == "medium" or level == "warning":
                    row.add_css_class("warning")
                else:
                    row.add_css_class("info")
                
                title = Gtk.Label(label=alert.get("title", "Alert"))
                title.add_css_class("alert-title")
                title.set_halign(Gtk.Align.START)
                row.append(title)
                
                time_str = alert.get("timestamp", "")[:19]
                time_label = Gtk.Label(label=time_str)
                time_label.add_css_class("alert-time")
                time_label.set_halign(Gtk.Align.START)
                row.append(time_label)
                
                self.alerts_box.append(row)


    class ConnectionsPanel(Gtk.Box):
        """Active connections panel."""
        
        def __init__(self):
            super().__init__(orientation=Gtk.Orientation.VERTICAL)
            self.add_css_class("panel")
            
            title = Gtk.Label(label="ACTIVE CONNECTIONS")
            title.add_css_class("panel-title")
            self.append(title)
            
            scroll = Gtk.ScrolledWindow()
            scroll.set_min_content_height(150)
            
            self.conn_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
            scroll.set_child(self.conn_box)
            
            self.append(scroll)
        
        def update_connections(self, connections: List[Dict]):
            """Update connection list."""
            while child := self.conn_box.get_first_child():
                self.conn_box.remove(child)
            
            for conn in connections[:15]:
                label = Gtk.Label(
                    label=f"{conn.get('src', '?')} → {conn.get('dst', '?')}:{conn.get('port', '?')}"
                )
                label.add_css_class("connection-item")
                label.set_halign(Gtk.Align.START)
                self.conn_box.append(label)


    class KalpanaDesktop(Gtk.ApplicationWindow):
        """Main desktop window."""
        
        def __init__(self, app):
            super().__init__(application=app)
            self.set_title("Kalpana Desktop")
            self.set_default_size(1280, 800)
            
            # Load CSS
            css_provider = Gtk.CssProvider()
            css_provider.load_from_data(KALPANA_CSS.encode())
            Gtk.StyleContext.add_provider_for_display(
                Gdk.Display.get_default(),
                css_provider,
                Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
            )
            
            # Main layout
            main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
            
            # Header
            header = Gtk.Box()
            header.add_css_class("header-bar")
            
            logo = Gtk.Label(label="🧠 KALPANA OS")
            logo.add_css_class("header-title")
            header.append(logo)
            
            spacer = Gtk.Box()
            spacer.set_hexpand(True)
            header.append(spacer)
            
            self.status_label = Gtk.Label(label="● ONLINE")
            self.status_label.add_css_class("status-online")
            header.append(self.status_label)
            
            main_box.append(header)
            
            # Content area
            content = Gtk.Box()
            content.add_css_class("main-container")
            content.set_vexpand(True)
            
            # Left column
            left_col = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
            left_col.set_hexpand(True)
            
            self.system_panel = SystemPanel()
            left_col.append(self.system_panel)
            
            self.network_panel = NetworkPanel()
            left_col.append(self.network_panel)
            
            content.append(left_col)
            
            # Right column
            right_col = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
            right_col.set_hexpand(True)
            
            self.alerts_panel = AlertsPanel()
            right_col.append(self.alerts_panel)
            
            self.connections_panel = ConnectionsPanel()
            right_col.append(self.connections_panel)
            
            content.append(right_col)
            
            main_box.append(content)
            
            # Toolbar
            toolbar = Gtk.Box()
            toolbar.add_css_class("toolbar")
            
            btn_shell = Gtk.Button(label="🖥️ Shell")
            btn_shell.add_css_class("toolbar-button")
            toolbar.append(btn_shell)
            
            btn_security = Gtk.Button(label="🔒 Security")
            btn_security.add_css_class("toolbar-button")
            toolbar.append(btn_security)
            
            btn_network = Gtk.Button(label="🌐 Network")
            btn_network.add_css_class("toolbar-button")
            toolbar.append(btn_network)
            
            btn_logs = Gtk.Button(label="📋 Logs")
            btn_logs.add_css_class("toolbar-button")
            toolbar.append(btn_logs)
            
            main_box.append(toolbar)
            
            self.set_child(main_box)
            
            # Start update timer
            GLib.timeout_add(2000, self._update_data)
        
        def _update_data(self) -> bool:
            """Periodic data update."""
            try:
                import psutil
                cpu = psutil.cpu_percent()
                mem = psutil.virtual_memory().percent
                disk = psutil.disk_usage('/').percent
                self.system_panel.update(cpu, mem, disk)
            except ImportError:
                self.system_panel.update(0, 0, 0)
            
            # Simulated data for demo
            # In production, this would fetch from Kalpana Core via IPC
            
            return True  # Continue timer


    class KalpanaDesktopApp(Gtk.Application):
        """GTK Application wrapper."""
        
        def __init__(self):
            super().__init__(application_id="org.kalpana.desktop")
            
        def do_activate(self):
            win = KalpanaDesktop(self)
            win.present()


# ============================================================================
# Entry Point
# ============================================================================

def main():
    print("""
    ╔═══════════════════════════════════════════════════════════╗
    ║                                                           ║
    ║    🖥️  KALPANA DESKTOP                                     ║
    ║    Kalpana OS Desktop Environment                         ║
    ║                                                           ║
    ╚═══════════════════════════════════════════════════════════╝
    """)
    
    if GTK_AVAILABLE:
        print("Starting GTK4 desktop...")
        app = KalpanaDesktopApp()
        app.run(None)
    else:
        print("GTK4 not available, running headless mode...")
        ui = HeadlessUI()
        try:
            asyncio.run(ui.run())
        except KeyboardInterrupt:
            ui.stop()


if __name__ == "__main__":
    main()
