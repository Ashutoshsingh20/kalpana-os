#!/usr/bin/env python3
"""
Kalpana OS - Linux System Tools
================================
Linux equivalent of macOS system control tools.
Uses D-Bus, XDG, and standard Linux utilities.
"""

import asyncio
import subprocess
import os
import shutil
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

@dataclass
class SystemInfo:
    """System information structure"""
    hostname: str
    kernel: str
    distro: str
    cpu: str
    memory_total: int
    memory_used: int
    disk_total: int
    disk_used: int
    uptime: str


class LinuxSystemTool:
    """
    Linux system control tool for Kalpana OS.
    Replaces macOS-specific AppleScript with Linux equivalents.
    """
    
    def __init__(self):
        self.desktop_env = self._detect_desktop()
    
    def _detect_desktop(self) -> str:
        """Detect current desktop environment."""
        de = os.environ.get("XDG_CURRENT_DESKTOP", "").lower()
        if "gnome" in de:
            return "gnome"
        elif "kde" in de or "plasma" in de:
            return "kde"
        elif "xfce" in de:
            return "xfce"
        else:
            return "generic"
    
    def _run_cmd(self, cmd: List[str], timeout: int = 10) -> str:
        """Run a shell command and return output."""
        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=timeout
            )
            return result.stdout.strip()
        except Exception as e:
            return f"Error: {e}"
    
    # ========== Application Control ==========
    
    async def open_app(self, app_name: str) -> bool:
        """Open an application."""
        # Try common launchers
        launchers = [
            ["gtk-launch", app_name],
            ["xdg-open", f"/usr/share/applications/{app_name}.desktop"],
            [app_name],  # Direct execution
        ]
        
        for launcher in launchers:
            try:
                subprocess.Popen(
                    launcher,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
                return True
            except:
                continue
        return False
    
    async def close_app(self, app_name: str) -> bool:
        """Close an application by name."""
        result = self._run_cmd(["pkill", "-f", app_name])
        return "Error" not in result
    
    async def focus_app(self, app_name: str) -> bool:
        """Bring application window to focus."""
        if self.desktop_env == "gnome":
            # Use wmctrl or xdotool
            self._run_cmd(["wmctrl", "-a", app_name])
        else:
            self._run_cmd(["xdotool", "search", "--name", app_name, "windowactivate"])
        return True
    
    async def list_running_apps(self) -> List[str]:
        """List running applications."""
        output = self._run_cmd(["ps", "-eo", "comm", "--no-headers"])
        return list(set(output.split('\n')))
    
    async def get_active_window(self) -> str:
        """Get currently focused window."""
        if shutil.which("xdotool"):
            window_id = self._run_cmd(["xdotool", "getactivewindow"])
            name = self._run_cmd(["xdotool", "getwindowname", window_id])
            return name
        return "Unknown"
    
    # ========== Volume Control ==========
    
    async def set_volume(self, level: int) -> bool:
        """Set system volume (0-100)."""
        level = max(0, min(100, level))
        
        # Try PulseAudio first, then ALSA
        if shutil.which("pactl"):
            self._run_cmd(["pactl", "set-sink-volume", "@DEFAULT_SINK@", f"{level}%"])
        elif shutil.which("amixer"):
            self._run_cmd(["amixer", "set", "Master", f"{level}%"])
        return True
    
    async def get_volume(self) -> int:
        """Get current volume level."""
        if shutil.which("pactl"):
            output = self._run_cmd(["pactl", "get-sink-volume", "@DEFAULT_SINK@"])
            # Parse output like "Volume: front-left: 65536 / 100% / ..."
            if "%" in output:
                import re
                match = re.search(r'(\d+)%', output)
                if match:
                    return int(match.group(1))
        return 50
    
    async def mute(self, muted: bool = True) -> bool:
        """Mute/unmute system audio."""
        state = "1" if muted else "0"
        if shutil.which("pactl"):
            self._run_cmd(["pactl", "set-sink-mute", "@DEFAULT_SINK@", state])
        elif shutil.which("amixer"):
            action = "mute" if muted else "unmute"
            self._run_cmd(["amixer", "set", "Master", action])
        return True
    
    # ========== Display Control ==========
    
    async def set_brightness(self, level: float) -> bool:
        """Set screen brightness (0.0 - 1.0)."""
        level = max(0.0, min(1.0, level))
        
        # Try xrandr for external displays
        if shutil.which("xrandr"):
            outputs = self._run_cmd(["xrandr", "--listmonitors"])
            # Get first monitor
            self._run_cmd(["xrandr", "--output", "eDP-1", "--brightness", str(level)])
        
        # Try brightnessctl for laptops
        if shutil.which("brightnessctl"):
            percent = int(level * 100)
            self._run_cmd(["brightnessctl", "set", f"{percent}%"])
        
        return True
    
    async def get_brightness(self) -> float:
        """Get current brightness."""
        if shutil.which("brightnessctl"):
            output = self._run_cmd(["brightnessctl", "get"])
            max_output = self._run_cmd(["brightnessctl", "max"])
            try:
                return int(output) / int(max_output)
            except:
                pass
        return 1.0
    
    async def sleep_display(self) -> bool:
        """Turn off display."""
        self._run_cmd(["xset", "dpms", "force", "off"])
        return True
    
    # ========== File Operations ==========
    
    async def open_file(self, file_path: str) -> bool:
        """Open a file with default application."""
        self._run_cmd(["xdg-open", file_path])
        return True
    
    async def open_url(self, url: str) -> bool:
        """Open URL in default browser."""
        self._run_cmd(["xdg-open", url])
        return True
    
    async def open_folder(self, folder_path: str) -> bool:
        """Open folder in file manager."""
        self._run_cmd(["xdg-open", folder_path])
        return True
    
    async def trash_file(self, file_path: str) -> bool:
        """Move file to trash."""
        if shutil.which("gio"):
            self._run_cmd(["gio", "trash", file_path])
        elif shutil.which("trash-put"):
            self._run_cmd(["trash-put", file_path])
        else:
            # Fallback: move to ~/.local/share/Trash
            trash_dir = Path.home() / ".local/share/Trash/files"
            trash_dir.mkdir(parents=True, exist_ok=True)
            shutil.move(file_path, trash_dir / Path(file_path).name)
        return True
    
    async def empty_trash(self) -> bool:
        """Empty the trash."""
        if shutil.which("gio"):
            self._run_cmd(["gio", "trash", "--empty"])
        elif shutil.which("trash-empty"):
            self._run_cmd(["trash-empty"])
        else:
            trash_dir = Path.home() / ".local/share/Trash/files"
            if trash_dir.exists():
                shutil.rmtree(trash_dir)
                trash_dir.mkdir()
        return True
    
    # ========== System Info ==========
    
    async def get_system_info(self) -> SystemInfo:
        """Get system information."""
        hostname = self._run_cmd(["hostname"])
        kernel = self._run_cmd(["uname", "-r"])
        
        # Get distro
        distro = "Linux"
        if os.path.exists("/etc/os-release"):
            with open("/etc/os-release") as f:
                for line in f:
                    if line.startswith("PRETTY_NAME="):
                        distro = line.split("=")[1].strip().strip('"')
                        break
        
        # CPU info
        cpu = "Unknown"
        if os.path.exists("/proc/cpuinfo"):
            with open("/proc/cpuinfo") as f:
                for line in f:
                    if "model name" in line:
                        cpu = line.split(":")[1].strip()
                        break
        
        # Memory
        mem_total = mem_used = 0
        if os.path.exists("/proc/meminfo"):
            with open("/proc/meminfo") as f:
                lines = f.readlines()
                for line in lines:
                    if "MemTotal" in line:
                        mem_total = int(line.split()[1]) * 1024
                    elif "MemAvailable" in line:
                        mem_avail = int(line.split()[1]) * 1024
                        mem_used = mem_total - mem_avail
        
        # Disk
        stat = os.statvfs("/")
        disk_total = stat.f_blocks * stat.f_frsize
        disk_used = (stat.f_blocks - stat.f_bfree) * stat.f_frsize
        
        # Uptime
        uptime = self._run_cmd(["uptime", "-p"])
        
        return SystemInfo(
            hostname=hostname,
            kernel=kernel,
            distro=distro,
            cpu=cpu,
            memory_total=mem_total,
            memory_used=mem_used,
            disk_total=disk_total,
            disk_used=disk_used,
            uptime=uptime
        )
    
    # ========== Notifications ==========
    
    async def show_notification(self, title: str, message: str, 
                                icon: str = "dialog-information") -> bool:
        """Show desktop notification."""
        self._run_cmd(["notify-send", "-i", icon, title, message])
        return True
    
    async def show_dialog(self, message: str, title: str = "Kalpana") -> Optional[str]:
        """Show dialog and get response."""
        if shutil.which("zenity"):
            result = self._run_cmd([
                "zenity", "--question", "--title", title, "--text", message
            ])
            return "yes" if result == "" else "no"
        elif shutil.which("kdialog"):
            result = self._run_cmd([
                "kdialog", "--yesno", message, "--title", title
            ])
            return "yes" if result == "" else "no"
        return None
    
    # ========== Clipboard ==========
    
    async def get_clipboard(self) -> str:
        """Get clipboard contents."""
        if shutil.which("xclip"):
            return self._run_cmd(["xclip", "-selection", "clipboard", "-o"])
        elif shutil.which("xsel"):
            return self._run_cmd(["xsel", "--clipboard", "--output"])
        elif shutil.which("wl-paste"):
            return self._run_cmd(["wl-paste"])
        return ""
    
    async def set_clipboard(self, text: str) -> bool:
        """Set clipboard contents."""
        if shutil.which("xclip"):
            proc = subprocess.Popen(
                ["xclip", "-selection", "clipboard"],
                stdin=subprocess.PIPE
            )
            proc.communicate(text.encode())
        elif shutil.which("xsel"):
            proc = subprocess.Popen(
                ["xsel", "--clipboard", "--input"],
                stdin=subprocess.PIPE
            )
            proc.communicate(text.encode())
        elif shutil.which("wl-copy"):
            proc = subprocess.Popen(
                ["wl-copy"],
                stdin=subprocess.PIPE
            )
            proc.communicate(text.encode())
        return True
    
    # ========== TTS ==========
    
    async def speak(self, text: str, voice: str = None) -> bool:
        """Speak text aloud."""
        if shutil.which("espeak-ng"):
            cmd = ["espeak-ng", text]
            if voice:
                cmd.extend(["-v", voice])
            subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        elif shutil.which("espeak"):
            subprocess.Popen(["espeak", text], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        elif shutil.which("festival"):
            proc = subprocess.Popen(
                ["festival", "--tts"],
                stdin=subprocess.PIPE
            )
            proc.communicate(text.encode())
        return True
    
    # ========== Screenshot ==========
    
    async def take_screenshot(self, path: str = None, region: bool = False) -> Optional[str]:
        """Take a screenshot."""
        if path is None:
            path = f"/tmp/screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        
        if shutil.which("gnome-screenshot"):
            cmd = ["gnome-screenshot", "-f", path]
            if region:
                cmd.append("-a")
            self._run_cmd(cmd)
        elif shutil.which("scrot"):
            cmd = ["scrot", path]
            if region:
                cmd.append("-s")
            self._run_cmd(cmd)
        elif shutil.which("grim"):  # Wayland
            self._run_cmd(["grim", path])
        
        return path if os.path.exists(path) else None
    
    # ========== Power Management ==========
    
    async def lock_screen(self) -> bool:
        """Lock the screen."""
        if self.desktop_env == "gnome":
            self._run_cmd(["gnome-screensaver-command", "-l"])
        elif self.desktop_env == "kde":
            self._run_cmd(["loginctl", "lock-session"])
        else:
            self._run_cmd(["xdg-screensaver", "lock"])
        return True
    
    async def suspend(self) -> bool:
        """Suspend the system."""
        self._run_cmd(["systemctl", "suspend"])
        return True
    
    async def shutdown(self) -> bool:
        """Shutdown the system."""
        self._run_cmd(["systemctl", "poweroff"])
        return True
    
    async def reboot(self) -> bool:
        """Reboot the system."""
        self._run_cmd(["systemctl", "reboot"])
        return True


def get_linux_system_tools() -> Dict[str, Dict[str, Any]]:
    """Get Linux system tools for registration."""
    tool = LinuxSystemTool()
    
    return {
        "open_app": {
            "func": tool.open_app,
            "description": "Open an application",
            "parameters": {"app_name": {"type": "string", "description": "Application name"}},
            "category": "system"
        },
        "close_app": {
            "func": tool.close_app,
            "description": "Close an application",
            "parameters": {"app_name": {"type": "string", "description": "Application name"}},
            "category": "system"
        },
        "set_volume": {
            "func": tool.set_volume,
            "description": "Set system volume (0-100)",
            "parameters": {"level": {"type": "integer", "description": "Volume level"}},
            "category": "system"
        },
        "get_volume": {
            "func": tool.get_volume,
            "description": "Get current volume level",
            "parameters": {},
            "category": "system"
        },
        "mute": {
            "func": tool.mute,
            "description": "Mute/unmute system audio",
            "parameters": {"muted": {"type": "boolean", "description": "True to mute"}},
            "category": "system"
        },
        "set_brightness": {
            "func": tool.set_brightness,
            "description": "Set screen brightness (0.0-1.0)",
            "parameters": {"level": {"type": "number", "description": "Brightness level"}},
            "category": "system"
        },
        "take_screenshot": {
            "func": tool.take_screenshot,
            "description": "Take a screenshot",
            "parameters": {
                "path": {"type": "string", "description": "Save path (optional)"},
                "region": {"type": "boolean", "description": "Select region"}
            },
            "category": "system"
        },
        "open_file": {
            "func": tool.open_file,
            "description": "Open a file with default application",
            "parameters": {"file_path": {"type": "string", "description": "File path"}},
            "category": "files"
        },
        "open_url": {
            "func": tool.open_url,
            "description": "Open URL in browser",
            "parameters": {"url": {"type": "string", "description": "URL to open"}},
            "category": "web"
        },
        "show_notification": {
            "func": tool.show_notification,
            "description": "Show desktop notification",
            "parameters": {
                "title": {"type": "string", "description": "Title"},
                "message": {"type": "string", "description": "Message body"}
            },
            "category": "system"
        },
        "get_clipboard": {
            "func": tool.get_clipboard,
            "description": "Get clipboard contents",
            "parameters": {},
            "category": "system"
        },
        "set_clipboard": {
            "func": tool.set_clipboard,
            "description": "Copy text to clipboard",
            "parameters": {"text": {"type": "string", "description": "Text to copy"}},
            "category": "system"
        },
        "speak": {
            "func": tool.speak,
            "description": "Speak text aloud using TTS",
            "parameters": {"text": {"type": "string", "description": "Text to speak"}},
            "category": "voice"
        },
        "get_system_info": {
            "func": tool.get_system_info,
            "description": "Get system information",
            "parameters": {},
            "category": "system"
        },
        "lock_screen": {
            "func": tool.lock_screen,
            "description": "Lock the screen",
            "parameters": {},
            "category": "system"
        },
        "trash_file": {
            "func": tool.trash_file,
            "description": "Move file to trash",
            "parameters": {"file_path": {"type": "string", "description": "File to trash"}},
            "category": "files"
        }
    }
