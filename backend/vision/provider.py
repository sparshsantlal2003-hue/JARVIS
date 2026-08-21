import json
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from PIL import Image
from backend.logger import setup_logger
from backend.config import settings

logger = setup_logger(__name__)

class VisionProvider(ABC):
    @abstractmethod
    def analyze_screen(self, image: Image.Image, query: str) -> str:
        pass

    @abstractmethod
    def locate_element(self, image: Image.Image, target: str) -> Optional[Dict[str, Any]]:
        pass

class OmniRouteVisionProvider(VisionProvider):
    def __init__(self):
        try:
            from groq import Groq
        except ImportError:
            logger.error("groq package not installed. Run 'pip install groq'.")
            raise
            
        api_key = getattr(settings, 'omniroute_api_key', None)
        base_url = getattr(settings, 'omniroute_base_url', 'http://localhost:20128/v1')
        
        self.client = Groq(api_key=api_key if api_key else "dummy_key", base_url=base_url)
        self.model_name = getattr(settings, 'omniroute_vision_model', 'gemini-flash-lite-latest')
        logger.info(f"[AI] Provider: OmniRoute | Route: vision | Model: {self.model_name} | Base URL: {base_url}")

    def _optimize_image(self, image: Image.Image) -> str:
        """Resizes, compresses, and base64-encodes the image."""
        if image.mode != "RGB":
            image = image.convert("RGB")
            
        max_size = 1024
        if max(image.size) > max_size:
            image.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
            
        import io
        import base64
        buf = io.BytesIO()
        image.save(buf, format="JPEG", quality=60, optimize=True)
        return base64.b64encode(buf.getvalue()).decode('utf-8')

    def analyze_screen(self, image: Image.Image, query: str) -> str:
        logger.info(f"[AI] Provider: OmniRoute | Route: vision | Image analysis started")
        b64_image = self._optimize_image(image)
        prompt = f"You are JARVIS's visual cortex. Briefly answer the user's query about this screenshot. Query: {query}"
        
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{b64_image}",
                        },
                    },
                ],
            }
        ]
        
        timeout = getattr(settings, 'omniroute_timeout', 60)
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=0.0,
                timeout=timeout
            )
            logger.info(f"[AI] Provider: OmniRoute | Route: vision | Image analysis completed")
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"[AI] Error calling OmniRoute Vision: {e}")
            return f"Error analyzing screen: {e}"

    def locate_element(self, image: Image.Image, target: str) -> Optional[Dict[str, Any]]:
        logger.info(f"[AI] Provider: OmniRoute | Route: vision | Element targeting started")
        b64_image = self._optimize_image(image)
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
                            "url": f"data:image/jpeg;base64,{b64_image}",
                        },
                    },
                ],
            }
        ]
        
        timeout = getattr(settings, 'omniroute_timeout', 60)
        try:
            # Note: response_format={"type": "json_object"} might not be supported by all OmniRoute models, 
            # so we request JSON in the prompt and parse it manually.
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=0.0,
                timeout=timeout
            )
            content = response.choices[0].message.content.strip()
            
            # Clean markdown code blocks if any
            if content.startswith("`json"):
                content = content[7:-3].strip()
            elif content.startswith("`"):
                content = content[3:-3].strip()
                
            import json
            data = json.loads(content)
            
            if "x" in data and "y" in data and "confidence" in data:
                logger.info(f"[AI] Provider: OmniRoute | Route: vision | Element targeting completed")
                return data
            return None
        except Exception as e:
            logger.error(f"[AI] Error in OmniRoute Vision targeting: {e}")
            return None

class GeminiVisionProvider(VisionProvider):
    def _optimize_image(self, image: Image.Image) -> Image.Image:
        """Resizes and compresses the image for significantly faster API uploads."""
        if image.mode != "RGB":
            image = image.convert("RGB")
            
        max_size = 1024
        if max(image.size) > max_size:
            image.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
            
        # We save it to bytes with lower quality just to force compression
        import io
        buf = io.BytesIO()
        image.save(buf, format="JPEG", quality=60, optimize=True)
        buf.seek(0)
        return Image.open(buf)

    def __init__(self):
        try:
            from google import genai
            from google.genai import types
        except ImportError:
            logger.error("google-genai package not installed. Run 'pip install google-genai'.")
            raise
            
        api_key = getattr(settings, 'gemini_api_key', None)
        if not api_key or api_key == "your_gemini_api_key_here":
            logger.warning("Gemini API key missing. Vision capabilities will fail.")
            
        # Initialize Gemini Client
        self.client = genai.Client(api_key=api_key)
        # We use flash as it's fast, free, and excellent at vision
        self.model_name = getattr(settings, "vision_model", "gemini-flash-latest")
        logger.info(f"GeminiVisionProvider initialized with model: {self.model_name}")

    def analyze_screen(self, image: Image.Image, query: str) -> str:
        prompt = f"You are JARVIS's visual cortex. Briefly answer the user's query about this screenshot. Query: {query}"
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=[prompt, self._optimize_image(image)],
                config={"temperature": 0.0}
            )
            return response.text.strip()
        except Exception as e:
            logger.error(f"Vision analysis failed: {e}")
            return f"Error analyzing screen: {e}"

    def locate_element(self, image: Image.Image, target: str) -> Optional[Dict[str, Any]]:
        width, height = image.size
        
        prompt = (
            f"You are JARVIS's visual targeting system. Locate '{target}' in this {width}x{height} screenshot. "
            "Reply strictly with a JSON object containing 'x', 'y' (the center coordinates of the element), "
            "and 'confidence' (a float between 0 and 1). If not found, return an empty JSON object {}. Do not include markdown formatting."
        )
        
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=[prompt, self._optimize_image(image)],
                config={
                    "temperature": 0.0,
                    "response_mime_type": "application/json"
                }
            )
            content = response.text.strip()
            
            data = json.loads(content)
            
            if "x" in data and "y" in data and "confidence" in data:
                return data
            return None
        except Exception as e:
            logger.error(f"Vision element targeting failed: {e}")
            return None


provider_name = getattr(settings, 'ai_provider', 'omniroute').lower()
if provider_name == 'omniroute':
    vision_provider = OmniRouteVisionProvider()
else:
    vision_provider = GeminiVisionProvider()

