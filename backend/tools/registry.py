from typing import Callable, Dict, Any, List
from backend.logger import setup_logger

logger = setup_logger(__name__)

class ToolRegistry:
    def __init__(self):
        self._tools: Dict[str, Callable] = {}
        self._tool_metadata: Dict[str, Dict[str, Any]] = {}

    def register(self, requires_confirmation: bool = False, risk_level: str = "LOW"):
        """Register a tool function with optional metadata."""
        
        # This handles the case where @registry.register is used without parentheses
        if callable(requires_confirmation):
            func = requires_confirmation
            self._tools[func.__name__] = func
            self._tool_metadata[func.__name__] = {
                "requires_confirmation": False,
                "risk_level": "LOW"
            }
            logger.debug(f"Registered tool: {func.__name__}")
            return func
            
        def decorator(func: Callable):
            self._tools[func.__name__] = func
            self._tool_metadata[func.__name__] = {
                "requires_confirmation": requires_confirmation,
                "risk_level": risk_level
            }
            logger.debug(f"Registered tool: {func.__name__} (risk: {risk_level}, confirm: {requires_confirmation})")
            return func
        return decorator

    def get_all_tools(self) -> List[Callable]:
        """Return all registered functions for the Gemini SDK."""
        return list(self._tools.values())

    def execute(self, tool_name: str, kwargs: Dict[str, Any]) -> Any:
        """Execute a registered tool by name with kwargs."""
        if tool_name not in self._tools:
            return {
                "success": False,
                "error": f"Tool '{tool_name}' not found in registry."
            }
            
        metadata = self._tool_metadata.get(tool_name, {})
        if metadata.get("requires_confirmation", False):
            # In Stage 3, we just log this. Future stages will pause and ask for confirmation.
            logger.info(f"Tool {tool_name} requires confirmation. Proceeding automatically in Stage 3.")
            
        try:
            kwargs = kwargs or {}
            logger.info(f"Executing tool: {tool_name} with args: {kwargs}")
            return self._tools[tool_name](**kwargs)
        except Exception as e:
            logger.error(f"Tool execution failed: {e}")
            return {
                "success": False,
                "error": f"Tool execution failed: {str(e)}"
            }

# Global registry instance
registry = ToolRegistry()
