#!/usr/bin/env python3
"""
Kalpana OS - Calendar & Reminders
==================================
Calendar management using local storage and system notifications.
Can integrate with GNOME Calendar, KDE Organizer, or standalone.
"""

import json
import subprocess
import shutil
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from pathlib import Path
from dataclasses import dataclass, asdict
import uuid


# Data directory
DATA_DIR = Path.home() / ".kalpana" / "data"
CALENDAR_FILE = DATA_DIR / "calendar.json"
REMINDERS_FILE = DATA_DIR / "reminders.json"

DATA_DIR.mkdir(parents=True, exist_ok=True)


@dataclass
class CalendarEvent:
    """Calendar event structure."""
    id: str
    title: str
    start: str  # ISO format
    end: str
    location: str = ""
    description: str = ""
    all_day: bool = False


@dataclass
class Reminder:
    """Reminder structure."""
    id: str
    title: str
    due: str  # ISO format
    completed: bool = False
    notes: str = ""


class CalendarManager:
    """Local calendar manager."""
    
    def __init__(self):
        self.events: List[Dict] = []
        self._load()
    
    def _load(self):
        if CALENDAR_FILE.exists():
            try:
                self.events = json.loads(CALENDAR_FILE.read_text())
            except:
                self.events = []
    
    def _save(self):
        CALENDAR_FILE.write_text(json.dumps(self.events, indent=2))
    
    async def create_event(self, title: str, start: str, end: str = None,
                          location: str = "", description: str = "",
                          all_day: bool = False) -> str:
        """Create a calendar event."""
        # Parse start time
        try:
            start_dt = datetime.fromisoformat(start)
        except:
            # Try natural format
            try:
                start_dt = datetime.strptime(start, "%Y-%m-%d %H:%M")
            except:
                return f"❌ Invalid date format: {start}"
        
        # Default end is 1 hour after start
        if end:
            try:
                end_dt = datetime.fromisoformat(end)
            except:
                end_dt = start_dt + timedelta(hours=1)
        else:
            end_dt = start_dt + timedelta(hours=1)
        
        event = {
            "id": str(uuid.uuid4())[:8],
            "title": title,
            "start": start_dt.isoformat(),
            "end": end_dt.isoformat(),
            "location": location,
            "description": description,
            "all_day": all_day
        }
        
        self.events.append(event)
        self._save()
        
        # Schedule notification
        await self._schedule_notification(event)
        
        return f"📅 Created event: {title} on {start_dt.strftime('%Y-%m-%d %H:%M')}"
    
    async def _schedule_notification(self, event: Dict):
        """Schedule a desktop notification for the event."""
        # Use at command or systemd timer
        pass  # Simplified for now
    
    async def get_today(self) -> str:
        """Get today's events."""
        self._load()
        today = datetime.now().date()
        
        today_events = []
        for e in self.events:
            try:
                event_date = datetime.fromisoformat(e["start"]).date()
                if event_date == today:
                    today_events.append(e)
            except:
                pass
        
        if not today_events:
            return "📅 No events scheduled for today"
        
        output = "**📅 Today's Events:**\n"
        for e in sorted(today_events, key=lambda x: x["start"]):
            time = datetime.fromisoformat(e["start"]).strftime("%H:%M")
            output += f"- {time}: {e['title']}"
            if e.get("location"):
                output += f" @ {e['location']}"
            output += "\n"
        
        return output
    
    async def get_upcoming(self, days: int = 7) -> str:
        """Get upcoming events."""
        self._load()
        now = datetime.now()
        end_date = now + timedelta(days=days)
        
        upcoming = []
        for e in self.events:
            try:
                event_dt = datetime.fromisoformat(e["start"])
                if now <= event_dt <= end_date:
                    upcoming.append(e)
            except:
                pass
        
        if not upcoming:
            return f"📅 No events in the next {days} days"
        
        output = f"**📅 Upcoming Events ({days} days):**\n"
        for e in sorted(upcoming, key=lambda x: x["start"]):
            dt = datetime.fromisoformat(e["start"])
            output += f"- {dt.strftime('%m/%d %H:%M')}: {e['title']}\n"
        
        return output
    
    async def delete_event(self, title_or_id: str) -> str:
        """Delete an event."""
        self._load()
        
        for i, e in enumerate(self.events):
            if e["id"] == title_or_id or title_or_id.lower() in e["title"].lower():
                removed = self.events.pop(i)
                self._save()
                return f"🗑️ Deleted event: {removed['title']}"
        
        return f"❌ Event not found: {title_or_id}"


class ReminderManager:
    """Local reminder manager."""
    
    def __init__(self):
        self.reminders: List[Dict] = []
        self._load()
    
    def _load(self):
        if REMINDERS_FILE.exists():
            try:
                self.reminders = json.loads(REMINDERS_FILE.read_text())
            except:
                self.reminders = []
    
    def _save(self):
        REMINDERS_FILE.write_text(json.dumps(self.reminders, indent=2))
    
    async def create_reminder(self, title: str, due: str = None, 
                             notes: str = "") -> str:
        """Create a reminder."""
        if due:
            try:
                due_dt = datetime.fromisoformat(due)
            except:
                try:
                    due_dt = datetime.strptime(due, "%Y-%m-%d %H:%M")
                except:
                    due_dt = None
        else:
            due_dt = None
        
        reminder = {
            "id": str(uuid.uuid4())[:8],
            "title": title,
            "due": due_dt.isoformat() if due_dt else None,
            "completed": False,
            "notes": notes
        }
        
        self.reminders.append(reminder)
        self._save()
        
        # Show notification
        if shutil.which("notify-send"):
            subprocess.run([
                "notify-send", "-i", "appointment-soon",
                "Reminder Set", title
            ])
        
        due_str = f" (due: {due_dt.strftime('%m/%d %H:%M')})" if due_dt else ""
        return f"⏰ Reminder created: {title}{due_str}"
    
    async def get_reminders(self, show_completed: bool = False) -> str:
        """Get reminders."""
        self._load()
        
        filtered = [r for r in self.reminders 
                   if show_completed or not r.get("completed")]
        
        if not filtered:
            return "⏰ No pending reminders"
        
        output = "**⏰ Reminders:**\n"
        for r in filtered:
            icon = "✅" if r.get("completed") else "⬜"
            output += f"{icon} `{r['id']}`: {r['title']}"
            if r.get("due"):
                due = datetime.fromisoformat(r["due"])
                output += f" (due: {due.strftime('%m/%d')})"
            output += "\n"
        
        return output
    
    async def complete_reminder(self, title_or_id: str) -> str:
        """Mark a reminder as completed."""
        self._load()
        
        for r in self.reminders:
            if r["id"] == title_or_id or title_or_id.lower() in r["title"].lower():
                r["completed"] = True
                self._save()
                return f"✅ Completed: {r['title']}"
        
        return f"❌ Reminder not found: {title_or_id}"


# Global instances
_calendar = CalendarManager()
_reminders = ReminderManager()


def get_calendar_tools() -> Dict[str, Dict[str, Any]]:
    """Get calendar and reminder tools."""
    return {
        "create_event": {
            "func": _calendar.create_event,
            "description": "Create a calendar event",
            "parameters": {
                "title": {"type": "string", "description": "Event title"},
                "start": {"type": "string", "description": "Start time (YYYY-MM-DD HH:MM)"},
                "end": {"type": "string", "description": "End time (optional)"},
                "location": {"type": "string", "description": "Location (optional)"}
            },
            "category": "calendar"
        },
        "get_today_events": {
            "func": _calendar.get_today,
            "description": "Get today's calendar events",
            "parameters": {},
            "category": "calendar"
        },
        "get_upcoming_events": {
            "func": _calendar.get_upcoming,
            "description": "Get upcoming events",
            "parameters": {"days": {"type": "integer", "description": "Days to look ahead"}},
            "category": "calendar"
        },
        "delete_event": {
            "func": _calendar.delete_event,
            "description": "Delete a calendar event",
            "parameters": {"title_or_id": {"type": "string", "description": "Event title or ID"}},
            "category": "calendar"
        },
        "create_reminder": {
            "func": _reminders.create_reminder,
            "description": "Create a reminder",
            "parameters": {
                "title": {"type": "string", "description": "Reminder title"},
                "due": {"type": "string", "description": "Due date/time (optional)"}
            },
            "category": "calendar"
        },
        "get_reminders": {
            "func": _reminders.get_reminders,
            "description": "Get pending reminders",
            "parameters": {},
            "category": "calendar"
        },
        "complete_reminder": {
            "func": _reminders.complete_reminder,
            "description": "Mark a reminder as done",
            "parameters": {"title_or_id": {"type": "string", "description": "Reminder title or ID"}},
            "category": "calendar"
        }
    }
