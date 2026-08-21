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
        self.model_name = "gemini-flash-latest"
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

vision_provider = GeminiVisionProvider()
