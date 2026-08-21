import base64
import json
import io
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from PIL import Image
from backend.logger import setup_logger
from backend.config import settings

logger = setup_logger(__name__)

class VisionProvider(ABC):
    @abstractmethod
    def analyze_screen(self, image: Image.Image, query: str) -> str:
        """Analyze the image and return a natural language description."""
        pass

    @abstractmethod
    def locate_element(self, image: Image.Image, target: str) -> Optional[Dict[str, Any]]:
        """
        Locate a specific element and return its coordinates and confidence.
        Expected return format: {"x": int, "y": int, "confidence": float}
        """
        pass

class GroqVisionProvider(VisionProvider):
    def __init__(self):
        try:
            from groq import Groq
        except ImportError:
            logger.error("groq package not installed. Run 'pip install groq'.")
            raise
            
        api_key = getattr(settings, 'groq_api_key', None)
        if not api_key or api_key == "your_groq_api_key_here":
            logger.warning("Groq API key missing. Vision capabilities will fail.")
            
        self.client = Groq(api_key=api_key)
        self.model_name = getattr(settings, 'vision_model', "llama-3.2-11b-vision-preview")
        logger.info(f"GroqVisionProvider initialized with model: {self.model_name}")

    def _encode_image(self, image: Image.Image) -> str:
        """Convert PIL Image to base64 string."""
        # Convert to RGB if necessary
        if image.mode != 'RGB':
            image = image.convert('RGB')
            
        buffered = io.BytesIO()
        # Compress image slightly to save tokens and fit within Groq's payload limits
        image.save(buffered, format="JPEG", quality=80)
        return base64.b64encode(buffered.getvalue()).decode('utf-8')

    def analyze_screen(self, image: Image.Image, query: str) -> str:
        base64_image = self._encode_image(image)
        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": f"You are JARVIS's visual cortex. Briefly answer the user's query about this screenshot. Query: {query}"
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}"
                        }
                    }
                ]
            }
        ]
        
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=0.0,
                max_tokens=256
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"Vision analysis failed: {e}")
            return f"Error analyzing screen: {e}"

    def locate_element(self, image: Image.Image, target: str) -> Optional[Dict[str, Any]]:
        base64_image = self._encode_image(image)
        width, height = image.size
        
        prompt = (
            f"You are JARVIS's visual targeting system. Locate '{target}' in this {width}x{height} screenshot. "
            "Reply strictly with a JSON object containing 'x', 'y' (the center coordinates of the element), "
            "and 'confidence' (a float between 0 and 1). If not found, return an empty JSON object {}. Do not include markdown formatting."
        )
        
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}"
                        }
                    }
                ]
            }
        ]
        
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=0.0,
                max_tokens=100
            )
            content = response.choices[0].message.content.strip()
            
            # Clean up potential markdown formatting from the response
            if content.startswith("`json"):
                content = content[7:]
            if content.endswith("`"):
                content = content[:-3]
                
            data = json.loads(content.strip())
            
            if "x" in data and "y" in data and "confidence" in data:
                return data
            return None
        except Exception as e:
            logger.error(f"Vision element targeting failed: {e}")
            return None

vision_provider = GroqVisionProvider()
