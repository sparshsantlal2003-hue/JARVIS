from typing import List, Dict, Any
from backend.provider import get_provider
from backend.logger import setup_logger
from backend.tools.registry import registry

logger = setup_logger(__name__)

class Agent:
    def __init__(self):
        self.provider = get_provider()
        self.history: List[Dict[str, Any]] = []
        logger.info("Agent initialized.")

    def chat(self, message: str) -> str:
        try:
            logger.debug(f"Received user message: {message}")
            self.history.append({"role": "user", "content": message})
            
            max_loops = 10
            previous_tool_calls = set()
            redundant_count = 0
            last_tool_result = None
            
            for _ in range(max_loops):
                try:
                    response = self.provider.generate_response(self.history)
                except Exception as e:
                    error_str = str(e)
                    if "tool_use_failed" in error_str or ("invalid_request_error" in error_str and "model_not_found" not in error_str):
                        logger.warning(f"AI generated malformed tool call. Prompting retry. Error: {error_str}")
                        self.history.append({
                            "role": "user",
                            "content": "SYSTEM ERROR: You generated a malformed tool call syntax. Please try again, and ensure you use correct formatting."
                        })
                        continue
                    raise e
                    
                if response["type"] == "text":
                    self.history.append({"role": "assistant", "content": response["content"]})
                    return response["content"]
                    
                elif response["type"] == "function_call":
                    tool_name = response["name"]
                    tool_args = response["args"]
                    
                    logger.info(f"AI requested tool call: {tool_name} with args {tool_args}")
                    
                    self.history.append({
                        "role": "assistant",
                        "function_calls": [{"name": tool_name, "args": tool_args}]
                    })
                    
                    tool_signature = f"{tool_name}:{str(tool_args)}"
                    if tool_signature in previous_tool_calls:
                        logger.warning(f"Prevented redundant tool call loop: {tool_signature}")
                        redundant_count += 1
                        if redundant_count >= 3:
                            return "JARVIS: I encountered an error and got stuck in a repetitive loop. Task safely aborted."
                        self.history.append({
                            "role": "user",
                            "function_responses": [{"name": tool_name, "response": {"success": False, "error": "SYSTEM ERROR: You already called this tool with these exact arguments. Stop calling tools and respond to the user with text."}}]
                        })
                        continue
                        
                    previous_tool_calls.add(tool_signature)
                    
                    result = registry.execute(tool_name, tool_args)
                    last_tool_result = result
                    
                    self.history.append({
                        "role": "user",
                        "function_responses": [{"name": tool_name, "response": result}]
                    })
                    
                    if isinstance(result, dict) and result.get("task_finished"):
                        return result.get("message", "Task completed.")
            
            # Last tool succeeded but AI kept looping — return terse confirmation
            if isinstance(last_tool_result, dict) and last_tool_result.get("success"):
                logger.warning("Agent hit loop limit after successful tool — returning Done.")
                return "Done."
            error_msg = "Agent exceeded maximum tool execution loops."
            logger.error(error_msg)
            return error_msg
            
        except Exception as e:
            error_str = str(e)
            logger.error(f"Agent encountered an error: {e}")
            return f"An unexpected error occurred: {error_str.split('Details:')[0][:200]}..."


