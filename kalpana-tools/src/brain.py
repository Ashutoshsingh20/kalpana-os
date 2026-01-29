#!/usr/bin/env python3
"""
Kalpana OS - AI Brain
======================
Natural language understanding and response generation.
Uses Ollama for local inference.
"""

import asyncio
import json
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False


@dataclass
class Intent:
    """Recognized intent from user input."""
    name: str
    confidence: float
    entities: Dict[str, Any]
    requires_tool: bool = False


@dataclass
class ConversationTurn:
    """Single turn in conversation."""
    role: str  # "user" or "assistant"
    content: str
    timestamp: datetime = field(default_factory=datetime.now)


class OllamaClient:
    """Client for local Ollama inference."""
    
    def __init__(self, host: str = "http://localhost:11434", model: str = "llama3.2"):
        self.host = host
        self.model = model
        self.available = False
        self._check_connection()
    
    def _check_connection(self):
        """Check if Ollama is available."""
        if not HTTPX_AVAILABLE:
            print("⚠️ httpx not available")
            return
        
        try:
            import requests
            response = requests.get(f"{self.host}/api/tags", timeout=2)
            if response.status_code == 200:
                self.available = True
                models = response.json().get("models", [])
                if models:
                    self.model = models[0].get("name", self.model)
                print(f"✅ Ollama connected, using model: {self.model}")
        except:
            print("⚠️ Ollama not available, using fallback mode")
    
    async def generate(self, prompt: str, system: str = "") -> str:
        """Generate response using Ollama."""
        if not self.available:
            return self._fallback_response(prompt)
        
        try:
            import requests
            response = requests.post(
                f"{self.host}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "system": system,
                    "stream": False
                },
                timeout=30
            )
            if response.status_code == 200:
                return response.json().get("response", "")
        except Exception as e:
            print(f"Ollama error: {e}")
        
        return self._fallback_response(prompt)
    
    def _fallback_response(self, prompt: str) -> str:
        """Simple fallback when Ollama is not available."""
        prompt_lower = prompt.lower()
        
        if "hello" in prompt_lower or "hi" in prompt_lower:
            return "Hello! I'm Kalpana, your AI assistant. How can I help you today?"
        elif "time" in prompt_lower:
            return f"The current time is {datetime.now().strftime('%H:%M:%S')}"
        elif "date" in prompt_lower:
            return f"Today is {datetime.now().strftime('%A, %B %d, %Y')}"
        elif "help" in prompt_lower:
            return "I can help you with: files, calendar, reminders, media control, system settings, and more. Just ask!"
        else:
            return "I understand. How can I assist you further?"


class KalpanaBrain:
    """Main AI brain for Kalpana OS."""
    
    INTENTS = {
        "file_operation": ["file", "folder", "directory", "move", "copy", "delete", "organize"],
        "calendar": ["event", "calendar", "schedule", "meeting", "appointment"],
        "reminder": ["remind", "reminder", "remember", "don't forget"],
        "media": ["play", "pause", "music", "song", "video", "spotify", "vlc"],
        "system": ["volume", "brightness", "screenshot", "lock", "shutdown", "reboot"],
        "web": ["search", "open", "browse", "website", "url"],
        "productivity": ["task", "todo", "note", "notes"],
        "vision": ["see", "look", "identify", "what is", "describe"],
        "greeting": ["hello", "hi", "hey", "good morning", "good afternoon"],
        "help": ["help", "what can you do", "how do i"],
    }
    
    SYSTEM_PROMPT = """You are Kalpana, an AI assistant integrated into Kalpana OS.
You are helpful, concise, and friendly. You help users with:
- File management and organization
- Calendar and reminders
- Media playback control
- System settings (volume, brightness)
- Vision and camera analysis
- General questions

Keep responses brief and actionable. If a task requires a tool, indicate which tool to use."""
    
    def __init__(self):
        self.ollama = OllamaClient()
        self.history: List[ConversationTurn] = []
        self.max_history = 20
    
    def _classify_intent(self, text: str) -> Intent:
        """Classify user intent from text."""
        text_lower = text.lower()
        
        for intent_name, keywords in self.INTENTS.items():
            for keyword in keywords:
                if keyword in text_lower:
                    return Intent(
                        name=intent_name,
                        confidence=0.8,
                        entities={},
                        requires_tool=intent_name not in ["greeting", "help"]
                    )
        
        return Intent(name="general", confidence=0.5, entities={})
    
    def _extract_entities(self, text: str, intent: Intent) -> Dict[str, Any]:
        """Extract entities from text based on intent."""
        entities = {}
        
        if intent.name == "file_operation":
            # Extract paths (simple heuristic)
            import re
            paths = re.findall(r'[~/][\w/.-]+', text)
            if paths:
                entities["path"] = paths[0]
        
        elif intent.name == "media":
            if "play" in text.lower():
                entities["action"] = "play"
            elif "pause" in text.lower():
                entities["action"] = "pause"
            elif "next" in text.lower():
                entities["action"] = "next"
        
        elif intent.name == "system":
            import re
            numbers = re.findall(r'\d+', text)
            if numbers:
                entities["level"] = int(numbers[0])
        
        return entities
    
    async def process_input(self, user_input: str) -> Tuple[str, Intent, Dict[str, Any]]:
        """Process user input and generate response."""
        # Add to history
        self.history.append(ConversationTurn(role="user", content=user_input))
        
        # Trim history
        if len(self.history) > self.max_history:
            self.history = self.history[-self.max_history:]
        
        # Classify intent
        intent = self._classify_intent(user_input)
        
        # Extract entities
        entities = self._extract_entities(user_input, intent)
        intent.entities = entities
        
        # Generate response
        context = "\n".join([
            f"{t.role}: {t.content}" for t in self.history[-5:]
        ])
        
        prompt = f"""Context:
{context}

User: {user_input}

Respond helpfully and concisely. If a specific tool or action is needed, indicate it clearly."""
        
        response = await self.ollama.generate(prompt, self.SYSTEM_PROMPT)
        
        # Add response to history
        self.history.append(ConversationTurn(role="assistant", content=response))
        
        return response, intent, entities
    
    async def generate_response(self, prompt: str) -> str:
        """Generate a response directly."""
        return await self.ollama.generate(prompt, self.SYSTEM_PROMPT)
    
    def get_tool_suggestion(self, intent: Intent) -> Optional[str]:
        """Suggest a tool based on intent."""
        tool_map = {
            "file_operation": "file_tools",
            "calendar": "calendar_tools",
            "reminder": "reminder_tools",
            "media": "media_tools",
            "system": "system_tools",
            "productivity": "productivity_tools",
            "vision": "vision_tools",
        }
        return tool_map.get(intent.name)


# Global instance
_brain = None

def get_brain() -> KalpanaBrain:
    """Get the Kalpana brain instance."""
    global _brain
    if _brain is None:
        _brain = KalpanaBrain()
    return _brain


def get_brain_tools() -> Dict[str, Dict[str, Any]]:
    """Get brain tools for registration."""
    brain = get_brain()
    
    async def ask_kalpana(question: str) -> str:
        response, _, _ = await brain.process_input(question)
        return response
    
    return {
        "ask_kalpana": {
            "func": ask_kalpana,
            "description": "Ask Kalpana a question or have a conversation",
            "parameters": {"question": {"type": "string", "description": "Your question or message"}},
            "category": "ai"
        }
    }
