from typing import List, Dict, Any
from backend.provider import get_provider
from backend.logger import setup_logger

logger = setup_logger(__name__)

class Agent:
    def __init__(self):
        self.provider = get_provider()
        self.history: List[Dict[str, Any]] = []
        logger.info("Agent initialized.")

    def chat(self, message: str) -> str:
        try:
            logger.debug(f"Received message: {message}")
            response = self.provider.generate_response(self.history, message)
            
            # Update history only on success
            self.history.append({"role": "user", "content": message})
            self.history.append({"role": "assistant", "content": response})
            
            return response
        except Exception as e:
            logger.error(f"Agent encountered an error: {e}")
            raise
