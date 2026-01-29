#!/usr/bin/env python3
"""
Kalpana OS - Voice System
==========================
Wake word detection, speech recognition, and TTS for Linux.
"""

import asyncio
import subprocess
import os
import shutil
from typing import Optional, Callable, Dict, Any
from pathlib import Path
import threading
import queue

try:
    import sounddevice as sd
    import numpy as np
    AUDIO_AVAILABLE = True
except ImportError:
    AUDIO_AVAILABLE = False

try:
    import whisper
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False


class WakeWordDetector:
    """Simple wake word detection using energy-based VAD."""
    
    def __init__(self, wake_word: str = "kalpana"):
        self.wake_word = wake_word.lower()
        self.is_listening = False
        self.callback = None
        self._thread = None
    
    def start(self, callback: Callable):
        """Start listening for wake word."""
        if not AUDIO_AVAILABLE:
            print("⚠️ sounddevice not available")
            return
        
        self.callback = callback
        self.is_listening = True
        self._thread = threading.Thread(target=self._listen_loop, daemon=True)
        self._thread.start()
        print(f"🎤 Listening for wake word: '{self.wake_word}'")
    
    def stop(self):
        """Stop listening."""
        self.is_listening = False
    
    def _listen_loop(self):
        """Main listening loop."""
        sample_rate = 16000
        chunk_duration = 3  # seconds
        
        while self.is_listening:
            try:
                # Record audio chunk
                audio = sd.rec(
                    int(chunk_duration * sample_rate),
                    samplerate=sample_rate,
                    channels=1,
                    dtype='float32'
                )
                sd.wait()
                
                # Check energy level (basic VAD)
                energy = np.abs(audio).mean()
                if energy > 0.01:  # Activity detected
                    # Transcribe and check for wake word
                    text = self._transcribe(audio, sample_rate)
                    if self.wake_word in text.lower():
                        if self.callback:
                            self.callback()
            except Exception as e:
                print(f"Audio error: {e}")
                break
    
    def _transcribe(self, audio: np.ndarray, sample_rate: int) -> str:
        """Transcribe audio using Whisper."""
        if not WHISPER_AVAILABLE:
            return ""
        
        try:
            model = whisper.load_model("tiny")
            result = model.transcribe(
                audio.flatten(),
                fp16=False,
                language="en"
            )
            return result.get("text", "")
        except:
            return ""


class SpeechRecognizer:
    """Speech to text using Whisper or system tools."""
    
    def __init__(self, model_size: str = "base"):
        self.model_size = model_size
        self.model = None
        
        if WHISPER_AVAILABLE:
            try:
                self.model = whisper.load_model(model_size)
                print(f"✅ Whisper {model_size} model loaded")
            except:
                print("⚠️ Could not load Whisper model")
    
    async def transcribe_file(self, audio_path: str) -> str:
        """Transcribe an audio file."""
        if self.model:
            try:
                result = self.model.transcribe(audio_path, fp16=False)
                return result.get("text", "").strip()
            except Exception as e:
                return f"Error: {e}"
        
        # Fallback to system tools
        if shutil.which("whisper"):
            result = subprocess.run(
                ["whisper", audio_path, "--output_format", "txt"],
                capture_output=True, text=True
            )
            return result.stdout.strip()
        
        return "Speech recognition not available"
    
    async def listen_and_transcribe(self, duration: int = 5) -> str:
        """Record and transcribe speech."""
        if not AUDIO_AVAILABLE:
            return "Audio recording not available"
        
        sample_rate = 16000
        print(f"🎤 Recording for {duration} seconds...")
        
        try:
            audio = sd.rec(
                int(duration * sample_rate),
                samplerate=sample_rate,
                channels=1,
                dtype='float32'
            )
            sd.wait()
            
            # Save to temp file
            import scipy.io.wavfile as wav
            temp_path = "/tmp/kalpana_recording.wav"
            wav.write(temp_path, sample_rate, (audio * 32767).astype(np.int16))
            
            return await self.transcribe_file(temp_path)
        except Exception as e:
            return f"Recording error: {e}"


class TextToSpeech:
    """Text to speech for Linux."""
    
    def __init__(self):
        self.engine = self._detect_engine()
    
    def _detect_engine(self) -> str:
        """Detect available TTS engine."""
        if shutil.which("espeak-ng"):
            return "espeak-ng"
        elif shutil.which("espeak"):
            return "espeak"
        elif shutil.which("festival"):
            return "festival"
        elif shutil.which("pico2wave"):
            return "pico"
        return None
    
    async def speak(self, text: str, voice: str = None) -> bool:
        """Speak text aloud."""
        if not self.engine:
            print(f"TTS: {text}")
            return False
        
        try:
            if self.engine in ["espeak-ng", "espeak"]:
                cmd = [self.engine]
                if voice:
                    cmd.extend(["-v", voice])
                cmd.append(text)
                subprocess.Popen(
                    cmd, 
                    stdout=subprocess.DEVNULL, 
                    stderr=subprocess.DEVNULL
                )
            
            elif self.engine == "festival":
                proc = subprocess.Popen(
                    ["festival", "--tts"],
                    stdin=subprocess.PIPE
                )
                proc.communicate(text.encode())
            
            elif self.engine == "pico":
                wav_file = "/tmp/kalpana_tts.wav"
                subprocess.run(["pico2wave", "-w", wav_file, text])
                subprocess.Popen(["aplay", wav_file])
            
            return True
        except Exception as e:
            print(f"TTS error: {e}")
            return False
    
    async def speak_async(self, text: str) -> None:
        """Speak text asynchronously."""
        await asyncio.to_thread(lambda: asyncio.run(self.speak(text)))


# Global instances
_wake_detector = None
_recognizer = None
_tts = None


def get_wake_detector() -> WakeWordDetector:
    global _wake_detector
    if _wake_detector is None:
        _wake_detector = WakeWordDetector()
    return _wake_detector


def get_recognizer() -> SpeechRecognizer:
    global _recognizer
    if _recognizer is None:
        _recognizer = SpeechRecognizer()
    return _recognizer


def get_tts() -> TextToSpeech:
    global _tts
    if _tts is None:
        _tts = TextToSpeech()
    return _tts


def get_voice_tools() -> Dict[str, Dict[str, Any]]:
    """Get voice tools for registration."""
    tts = get_tts()
    recognizer = get_recognizer()
    
    return {
        "speak": {
            "func": tts.speak,
            "description": "Speak text aloud using TTS",
            "parameters": {
                "text": {"type": "string", "description": "Text to speak"},
                "voice": {"type": "string", "description": "Voice to use (optional)"}
            },
            "category": "voice"
        },
        "transcribe_audio": {
            "func": recognizer.transcribe_file,
            "description": "Transcribe an audio file to text",
            "parameters": {
                "audio_path": {"type": "string", "description": "Path to audio file"}
            },
            "category": "voice"
        },
        "listen_and_transcribe": {
            "func": recognizer.listen_and_transcribe,
            "description": "Record and transcribe speech",
            "parameters": {
                "duration": {"type": "integer", "description": "Recording duration in seconds"}
            },
            "category": "voice"
        }
    }
