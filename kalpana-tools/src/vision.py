#!/usr/bin/env python3
"""
Kalpana OS - Vision Tools
==========================
Object detection and image analysis using OpenCV + YOLO.
"""

import cv2
import numpy as np
from typing import Optional, List, Tuple, Dict, Any
from pathlib import Path
import urllib.request
import os


class VisionTool:
    """Image analysis using OpenCV + pre-trained models."""
    
    # COCO class names
    CLASSES = [
        "person", "bicycle", "car", "motorcycle", "airplane", "bus", "train", "truck",
        "boat", "traffic light", "fire hydrant", "stop sign", "parking meter", "bench",
        "bird", "cat", "dog", "horse", "sheep", "cow", "elephant", "bear", "zebra",
        "giraffe", "backpack", "umbrella", "handbag", "tie", "suitcase", "frisbee",
        "skis", "snowboard", "sports ball", "kite", "baseball bat", "baseball glove",
        "skateboard", "surfboard", "tennis racket", "bottle", "wine glass", "cup",
        "fork", "knife", "spoon", "bowl", "banana", "apple", "sandwich", "orange",
        "broccoli", "carrot", "hot dog", "pizza", "donut", "cake", "chair", "couch",
        "potted plant", "bed", "dining table", "toilet", "tv", "laptop", "mouse",
        "remote", "keyboard", "cell phone", "microwave", "oven", "toaster", "sink",
        "refrigerator", "book", "clock", "vase", "scissors", "teddy bear", "hair drier",
        "toothbrush"
    ]
    
    def __init__(self):
        self.model_dir = Path.home() / ".kalpana" / "models"
        self.model_dir.mkdir(parents=True, exist_ok=True)
        self.net = None
        self._load_models()
    
    def _load_models(self):
        """Download and load YOLO model."""
        weights = self.model_dir / "yolov3-tiny.weights"
        cfg = self.model_dir / "yolov3-tiny.cfg"
        
        # Download if not exists
        base_url = "https://pjreddie.com/media/files/"
        cfg_url = "https://raw.githubusercontent.com/pjreddie/darknet/master/cfg/yolov3-tiny.cfg"
        
        if not weights.exists():
            print("📥 Downloading YOLO weights...")
            try:
                urllib.request.urlretrieve(
                    f"{base_url}yolov3-tiny.weights", str(weights)
                )
            except:
                print("⚠️ Could not download weights")
                return
        
        if not cfg.exists():
            print("📥 Downloading YOLO config...")
            try:
                urllib.request.urlretrieve(cfg_url, str(cfg))
            except:
                print("⚠️ Could not download config")
                return
        
        # Load model
        try:
            self.net = cv2.dnn.readNetFromDarknet(str(cfg), str(weights))
            self.net.setPreferableBackend(cv2.dnn.DNN_BACKEND_OPENCV)
            print("✅ Vision model loaded")
        except Exception as e:
            print(f"⚠️ Could not load model: {e}")
    
    def _detect_objects(self, image_path: str, 
                        confidence_threshold: float = 0.5) -> List[Tuple[str, float]]:
        """Detect objects in image using YOLO."""
        if self.net is None:
            return []
        
        # Load image
        img = cv2.imread(image_path)
        if img is None:
            return []
        
        height, width = img.shape[:2]
        
        # Create blob
        blob = cv2.dnn.blobFromImage(
            img, 1/255.0, (416, 416), swapRB=True, crop=False
        )
        
        self.net.setInput(blob)
        
        # Get output layer names
        layer_names = self.net.getLayerNames()
        output_layers = [layer_names[i - 1] for i in self.net.getUnconnectedOutLayers()]
        
        # Forward pass
        outputs = self.net.forward(output_layers)
        
        # Parse detections
        detections = []
        for output in outputs:
            for detection in output:
                scores = detection[5:]
                class_id = np.argmax(scores)
                confidence = scores[class_id]
                
                if confidence > confidence_threshold:
                    class_name = self.CLASSES[class_id] if class_id < len(self.CLASSES) else "unknown"
                    detections.append((class_name, float(confidence)))
        
        # Remove duplicates, keep highest confidence
        seen = {}
        for name, conf in detections:
            if name not in seen or conf > seen[name]:
                seen[name] = conf
        
        return [(k, v) for k, v in sorted(seen.items(), key=lambda x: -x[1])]
    
    async def identify_objects(self, image_path: Optional[str] = None) -> str:
        """Identify objects in an image."""
        if image_path is None:
            # Try to capture from camera
            image_path = "/tmp/kalpana_capture.jpg"
            cap = cv2.VideoCapture(0)
            ret, frame = cap.read()
            cap.release()
            if ret:
                cv2.imwrite(image_path, frame)
            else:
                return "❌ No camera available and no image provided"
        
        if not Path(image_path).exists():
            return f"❌ Image not found: {image_path}"
        
        detections = self._detect_objects(image_path)
        
        if not detections:
            return "🔍 No objects detected"
        
        output = "**🔍 Objects Detected:**\n"
        for name, conf in detections[:10]:
            output += f"- {name}: {conf*100:.1f}% confidence\n"
        
        return output
    
    async def describe_scene(self, image_path: Optional[str] = None) -> str:
        """Generate a scene description."""
        if image_path is None:
            image_path = "/tmp/kalpana_capture.jpg"
            cap = cv2.VideoCapture(0)
            ret, frame = cap.read()
            cap.release()
            if ret:
                cv2.imwrite(image_path, frame)
            else:
                return "❌ No camera available"
        
        detections = self._detect_objects(image_path, confidence_threshold=0.3)
        
        if not detections:
            return "I see an image but couldn't identify specific objects."
        
        # Build natural description
        objects = [name for name, _ in detections[:5]]
        
        if len(objects) == 1:
            description = f"I can see a {objects[0]}."
        elif len(objects) == 2:
            description = f"I can see a {objects[0]} and a {objects[1]}."
        else:
            description = f"I can see {', '.join(objects[:-1])}, and {objects[-1]}."
        
        # Add context
        if "person" in objects:
            description += " There appears to be a person in the scene."
        
        return f"📷 **Scene Description:**\n{description}"
    
    async def what_am_i_holding(self) -> str:
        """Identify what's being held (via camera)."""
        return await self.identify_objects()


# Global instance
_vision = None

def get_vision() -> VisionTool:
    """Get or create vision tool instance."""
    global _vision
    if _vision is None:
        _vision = VisionTool()
    return _vision


def get_vision_tools() -> Dict[str, Dict[str, Any]]:
    """Get vision tools for registration."""
    vision = get_vision()
    
    return {
        "identify_objects": {
            "func": vision.identify_objects,
            "description": "Identify objects in an image or camera capture",
            "parameters": {
                "image_path": {"type": "string", "description": "Image path (optional, uses camera if not provided)"}
            },
            "category": "vision"
        },
        "describe_scene": {
            "func": vision.describe_scene,
            "description": "Describe what's visible in an image",
            "parameters": {
                "image_path": {"type": "string", "description": "Image path (optional)"}
            },
            "category": "vision"
        },
        "what_am_i_holding": {
            "func": vision.what_am_i_holding,
            "description": "Identify what's being held (camera capture)",
            "parameters": {},
            "category": "vision"
        }
    }
