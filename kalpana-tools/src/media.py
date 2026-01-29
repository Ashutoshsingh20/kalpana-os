#!/usr/bin/env python3
"""
Kalpana OS - Media Control Tools
=================================
Control media players on Linux using MPRIS D-Bus interface.
Works with Spotify, VLC, Rhythmbox, and any MPRIS-compatible player.
"""

import subprocess
import shutil
from typing import Dict, Any, Optional


class MediaController:
    """Control media players via MPRIS D-Bus interface."""
    
    def __init__(self):
        self.dbus_available = shutil.which("dbus-send") is not None
        self.playerctl_available = shutil.which("playerctl") is not None
    
    def _run_playerctl(self, action: str, player: str = None) -> str:
        """Run playerctl command."""
        if not self.playerctl_available:
            return "playerctl not available"
        
        cmd = ["playerctl"]
        if player:
            cmd.extend(["-p", player])
        cmd.append(action)
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            return result.stdout.strip() or result.stderr.strip() or "Done"
        except Exception as e:
            return f"Error: {e}"
    
    async def play(self, player: str = None) -> str:
        """Play/resume media."""
        return self._run_playerctl("play", player)
    
    async def pause(self, player: str = None) -> str:
        """Pause media."""
        return self._run_playerctl("pause", player)
    
    async def play_pause(self, player: str = None) -> str:
        """Toggle play/pause."""
        return self._run_playerctl("play-pause", player)
    
    async def next_track(self, player: str = None) -> str:
        """Skip to next track."""
        return self._run_playerctl("next", player)
    
    async def previous_track(self, player: str = None) -> str:
        """Go to previous track."""
        return self._run_playerctl("previous", player)
    
    async def stop(self, player: str = None) -> str:
        """Stop playback."""
        return self._run_playerctl("stop", player)
    
    async def get_status(self, player: str = None) -> str:
        """Get current playback status."""
        status = self._run_playerctl("status", player)
        title = self._run_playerctl("metadata title", player)
        artist = self._run_playerctl("metadata artist", player)
        
        return f"""**🎵 Now Playing:**
- Status: {status}
- Title: {title}
- Artist: {artist}"""
    
    async def set_volume(self, level: float, player: str = None) -> str:
        """Set player volume (0.0-1.0)."""
        level = max(0.0, min(1.0, level))
        return self._run_playerctl(f"volume {level}", player)
    
    async def list_players(self) -> str:
        """List available media players."""
        result = self._run_playerctl("-l")
        if not result or "Error" in result:
            return "No active media players found"
        return f"**Active Players:**\n{result}"


class SpotifyController(MediaController):
    """Spotify-specific controls."""
    
    def __init__(self):
        super().__init__()
        self.player = "spotify"
    
    async def play_track(self, search: str) -> str:
        """Search and play a track on Spotify."""
        # Open Spotify search in browser (will prompt to open in app)
        search_url = f"spotify:search:{search.replace(' ', '%20')}"
        subprocess.Popen(["xdg-open", search_url])
        return f"🎵 Searching Spotify for: {search}"
    
    async def play_playlist(self, playlist_name: str) -> str:
        """Play a playlist."""
        return await self.play_track(playlist_name)
    
    async def current_track(self) -> str:
        """Get current Spotify track."""
        return await self.get_status(self.player)


class VLCController:
    """VLC-specific controls via command line."""
    
    def __init__(self):
        self.vlc_path = shutil.which("vlc") or shutil.which("cvlc")
    
    async def play_file(self, file_path: str) -> str:
        """Play a media file in VLC."""
        if not self.vlc_path:
            return "VLC not installed"
        
        try:
            subprocess.Popen(
                [self.vlc_path, file_path],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            return f"▶️ Playing: {file_path}"
        except Exception as e:
            return f"Error: {e}"
    
    async def play_url(self, url: str) -> str:
        """Play a stream URL in VLC."""
        return await self.play_file(url)


# Global instances
_media = None
_spotify = None
_vlc = None


def get_media_controller() -> MediaController:
    global _media
    if _media is None:
        _media = MediaController()
    return _media


def get_spotify_controller() -> SpotifyController:
    global _spotify
    if _spotify is None:
        _spotify = SpotifyController()
    return _spotify


def get_vlc_controller() -> VLCController:
    global _vlc
    if _vlc is None:
        _vlc = VLCController()
    return _vlc


def get_media_tools() -> Dict[str, Dict[str, Any]]:
    """Get media control tools for registration."""
    media = get_media_controller()
    spotify = get_spotify_controller()
    vlc = get_vlc_controller()
    
    return {
        "media_play": {
            "func": media.play,
            "description": "Play/resume media playback",
            "parameters": {"player": {"type": "string", "description": "Player name (optional)"}},
            "category": "media"
        },
        "media_pause": {
            "func": media.pause,
            "description": "Pause media playback",
            "parameters": {"player": {"type": "string", "description": "Player name (optional)"}},
            "category": "media"
        },
        "media_next": {
            "func": media.next_track,
            "description": "Skip to next track",
            "parameters": {"player": {"type": "string", "description": "Player name (optional)"}},
            "category": "media"
        },
        "media_previous": {
            "func": media.previous_track,
            "description": "Go to previous track",
            "parameters": {"player": {"type": "string", "description": "Player name (optional)"}},
            "category": "media"
        },
        "media_status": {
            "func": media.get_status,
            "description": "Get current playback status",
            "parameters": {},
            "category": "media"
        },
        "spotify_play": {
            "func": spotify.play_track,
            "description": "Search and play on Spotify",
            "parameters": {"search": {"type": "string", "description": "Song/artist to search"}},
            "category": "media"
        },
        "vlc_play_file": {
            "func": vlc.play_file,
            "description": "Play a media file in VLC",
            "parameters": {"file_path": {"type": "string", "description": "Path to media file"}},
            "category": "media"
        },
        "vlc_play_url": {
            "func": vlc.play_url,
            "description": "Play a stream URL in VLC",
            "parameters": {"url": {"type": "string", "description": "Stream URL"}},
            "category": "media"
        },
        "list_players": {
            "func": media.list_players,
            "description": "List active media players",
            "parameters": {},
            "category": "media"
        }
    }
