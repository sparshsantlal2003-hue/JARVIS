import re
import re
import ast
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from google import genai
from google.genai import types
import json
import re

from backend.config import settings
from backend.logger import setup_logger
from backend.tools.registry import registry
import backend.tools.windows_apps  # Ensures tools are registered
import backend.tools.browser       # Ensures browser tools are registered

logger = setup_logger(__name__)

class AIProvider(ABC):
    @abstractmethod
    def generate_response(self, history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate a response given the entire conversation history."""
        pass

class MockProvider(AIProvider):
    def generate_response(self, history: List[Dict[str, Any]]) -> Dict[str, Any]:
        last_msg = history[-1].get("content", "")
        logger.info(f"MockProvider processing message: {last_msg}")
        return {"type": "text", "content": f"This is a mock response to: '{last_msg}'"}

class GeminiProvider(AIProvider):
    def __init__(self):
        if not settings.gemini_api_key or settings.gemini_api_key == "your_gemini_api_key_here":
            logger.warning("Gemini API key is missing or default. Please configure GEMINI_API_KEY.")
        self.client = genai.Client(api_key=settings.gemini_api_key)
        self.model_name = "gemini-flash-latest"
        logger.info(f"GeminiProvider initialized with model: {self.model_name}")

    def generate_response(self, history: List[Dict[str, Any]]) -> Dict[str, Any]:
        contents = []
        
        import os
        import pathlib
        home_dir = pathlib.Path.home().as_posix()
        desktop_dir = (pathlib.Path.home() / "Desktop").as_posix()
        
        strong_instruction = (
            "CRITICAL DIRECTIVE: You are JARVIS, a highly advanced desktop AI assistant. You are NOT Gemini. "
            "You are NOT a large language model. You are JARVIS. Whenever asked about your identity, name, creator, "
            "or who you are, you MUST reply ONLY with 'My name is JARVIS, your intelligent desktop AI assistant.' "
            "Do not mention Google, do not mention Gemini.\n\n"
            "ENVIRONMENT VARIABLES:\n"
            f"The user's home directory is: {home_dir}\n"
            f"The user's Desktop directory is: {desktop_dir}\n\n"
            "CRITICAL TOOL INSTRUCTION:\n"
            "If a tool call returns a JSON response where 'success' is false, you MUST report the failure to the user and explain why. "
            "NEVER claim a tool succeeded if it actually failed.\n"
            "STRICT RULE: DO NOT execute any interactive tools (like typing text or clicking) unless the user EXPLICITLY asks you to. "
            "Opening an application does NOT mean you should automatically start typing in it.\n"
            "STRICT RULE: Once you have successfully executed the necessary tools to fulfill the user's command (like scrolling, playing a video, or typing), YOU MUST STOP CALLING TOOLS IMMEDIATELY! DO NOT navigate to Google! Just output a final text message or use the finish_task tool! "
            "Do not call the same tool twice unless explicitly requested. You MUST reply with a final text message to the user acknowledging completion. "
            "CONCISENESS RULE: You MUST be extremely concise to save API tokens. When executing a command, NEVER explain your process, NEVER explain how you did it, and NEVER summarize the results unless explicitly asked. Your final response should be a maximum of 1 or 2 short sentences simply confirming the action is done.\n" \
              "TYPING INSTRUCTION: When asked to type a sentence multiple times, you must separate each repetition with a space, NOT a newline! ONLY use newlines if the user explicitly asks you to type them on new lines or press enter.\n"
            "BROWSER USAGE: When instructed to use the browser, you must sequence your tool calls correctly (e.g. search_web first, then read_page, then stop).\n" \
            "SEARCH INSTRUCTION: When the user asks to 'open the first result', DO NOT use click_element. You MUST read the 'url' from the search_web JSON results and use the navigate(url) tool to open it directly!\n" \
            "NOTEPAD INSTRUCTION: When the user asks you to type something in Notepad, you MUST first use keyboard_action('ctrl+n') to open a new tab in Notepad before typing. NEVER type into an existing saved file/tab. NEVER open Brave or any browser after completing a typing task unless the user explicitly requests it. After type_text() returns success, you MUST immediately output a final text reply (e.g. 'Done.') and stop calling any further tools.\n" \
            "YOUTUBE INSTRUCTION: To play or pause a video, you MUST use keyboard_action('k'). NEVER use go_back or Space! If the user asks to search for something ON YouTube, DO NOT use search_web! You MUST use the navigate tool with the URL https://www.youtube.com/results?search_query=... directly!"
        )
        
        contents.append(types.Content(role="user", parts=[types.Part.from_text(text=strong_instruction)]))
        contents.append(types.Content(role="model", parts=[types.Part.from_text(text="Understood. I am JARVIS, your intelligent desktop AI assistant.")]))
        
        
        # Intelligent history retention:
        # Keep System Prompt [0]
        # Keep the most recent explicit User message (not a tool result)
        # Keep the last 6 messages
        
        if len(history) > 7:
            processed_history = [history[0]]
            
            # Find the most recent explicit user message
            last_explicit_user_msg = None
            for msg in reversed(history[1:-6]):
                if msg["role"] == "user":
                    if "function_responses" not in msg and not (isinstance(msg.get("content"), str) and msg["content"].startswith("[Tool Result")):
                        last_explicit_user_msg = msg
                        break
                        
            if last_explicit_user_msg:
                processed_history.append(last_explicit_user_msg)
                
            processed_history.extend(history[-6:])
        else:
            processed_history = history


        
        for msg in processed_history:
            role = "user" if msg["role"] == "user" else "model"
            
            parts = []
            if "content" in msg and msg["content"]:
                parts.append(types.Part.from_text(text=msg["content"]))
                
            if "function_calls" in msg:
                for fc in msg["function_calls"]:
                    parts.append(types.Part.from_function_call(name=fc["name"], args=fc["args"]))
                    
            if "function_responses" in msg:
                for fr in msg["function_responses"]:
                    parts.append(types.Part.from_function_response(name=fr["name"], response=fr["response"]))
            
            if parts:
                contents.append(types.Content(role=role, parts=parts))
        
        try:
            tools = registry.get_all_tools()
            config = types.GenerateContentConfig(
                temperature=0.0,
                tools=tools if tools else None
            )
            
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=contents,
                config=config
            )
            
            if response.function_calls:
                fc = response.function_calls[0]
                return {
                    "type": "function_call",
                    "name": fc.name,
                    "args": fc.args
                }
            else:
                # Fallback for LLaMA 8B text-leaked tool calls
                if message.content:
                    match = re.search(r"<(\w+)>(\{.*?\})</\1>", message.content, re.DOTALL)
                    if match:
                        tool_name = match.group(1)
                        tool_args_str = match.group(2).strip()
                        try:
                            tool_args = json.loads(tool_args_str)
                        except Exception:
                            try:
                                tool_args = ast.literal_eval(tool_args_str)
                            except Exception:
                                tool_args = {}
                        logger.info(f"Successfully rescued leaked text tool call: {tool_name}")
                        return {"type": "function_call", "name": tool_name, "args": tool_args}
                        
                    match3 = re.search(r"\[Tool Call Executed:\s+(\w+)(?:\s+with args\s+(\{.*?\}))?\]", message.content, re.DOTALL)
                    if match3:
                        tool_name = match3.group(1)
                        tool_args_str = match3.group(2).strip() if match3.group(2) else ''
                        try:
                            tool_args = json.loads(tool_args_str.replace("'", '"'))
                        except Exception:
                            try:
                                tool_args = ast.literal_eval(tool_args_str)
                            except Exception:
                                tool_args = {}
                        logger.info(f"Successfully rescued history-mimicked text tool call: {tool_name}")
                        return {"type": "function_call", "name": tool_name, "args": tool_args}
                        
                    match2 = re.search(r"<function=(\w+)[^>]*?>(\{.*?\})", message.content, re.DOTALL)
                    if match2:
                        tool_name = match2.group(1)
                        tool_args_str = match2.group(2).strip()
                        try:
                            tool_args = json.loads(tool_args_str)
                        except Exception:
                            try:
                                tool_args = ast.literal_eval(tool_args_str)
                            except Exception:
                                tool_args = {}
                        logger.info(f"Successfully rescued leaked text tool call (format 2): {tool_name}")
                        return {"type": "function_call", "name": tool_name, "args": tool_args}
                        
                return {"type": "text", "content": message.content}
                
        except Exception as e:
            error_str = str(e)
            if "429" in error_str and "RESOURCE_EXHAUSTED" in error_str:
                logger.error("Error calling Gemini: 429 RESOURCE_EXHAUSTED (Rate limit exceeded)")
            elif "503" in error_str and "UNAVAILABLE" in error_str:
                logger.error("Error calling Gemini: 503 UNAVAILABLE (Server Overloaded)")
            else:
                logger.error(f"Error calling Gemini: {e}")
            raise

class GroqProvider(AIProvider):
    def __init__(self):
        try:
            from groq import Groq
        except ImportError:
            logger.error("groq package not installed. Run 'pip install groq'.")
            raise
            
        if not getattr(settings, 'groq_api_key', None) or settings.groq_api_key == "your_groq_api_key_here":
            logger.warning("Groq API key is missing or default. Please configure GROQ_API_KEY in .env.")
            
        self.client = Groq(api_key=getattr(settings, 'groq_api_key', None))
        self.model_name = settings.groq_model
        logger.info(f"GroqProvider initialized with model: {self.model_name}")

    def generate_response(self, history: List[Dict[str, Any]]) -> Dict[str, Any]:
        messages = []
        
        import os
        import pathlib
        from backend.schema import function_to_json_schema
        
        home_dir = pathlib.Path.home().as_posix()
        desktop_dir = (pathlib.Path.home() / 'Desktop').as_posix()
        
        strong_instruction = (
            "CRITICAL DIRECTIVE: You are JARVIS, a highly advanced desktop AI assistant. "
            "You are NOT a large language model. You are JARVIS. Whenever asked about your identity, name, creator, "
            "or who you are, you MUST reply ONLY with 'My name is JARVIS, your intelligent desktop AI assistant.'\n\n"
            "ENVIRONMENT VARIABLES:\n"
            f"The user's home directory is: {home_dir}\n"
            f"The user's Desktop directory is: {desktop_dir}\n\n"
            "CRITICAL TOOL INSTRUCTION:\n"
            "If a tool call returns a JSON response where 'success' is false, you MUST report the failure to the user and explain why. "
            "NEVER claim a tool succeeded if it actually failed.\n"
            "STRICT RULE: DO NOT execute any interactive tools (like typing text or clicking) unless the user EXPLICITLY asks you to. "
            "Opening an application does NOT mean you should automatically start typing in it.\n"
            "STRICT RULE: Once you have successfully executed the necessary tools to fulfill the user's command (like scrolling, playing a video, or typing), YOU MUST STOP CALLING TOOLS IMMEDIATELY! DO NOT navigate to Google! Just output a final text message or use the finish_task tool! "
            "Do not call the same tool twice unless explicitly requested. You MUST reply with a final text message to the user acknowledging completion. "
            "CONCISENESS RULE: You MUST be extremely concise to save API tokens. When executing a command, NEVER explain your process, NEVER explain how you did it, and NEVER summarize the results unless explicitly asked. Your final response should be a maximum of 1 or 2 short sentences simply confirming the action is done.\n" \
              "TYPING INSTRUCTION: When asked to type a sentence multiple times, you must separate each repetition with a space, NOT a newline! ONLY use newlines if the user explicitly asks you to type them on new lines or press enter.\n"
            "BROWSER USAGE: When instructed to use the browser, you must sequence your tool calls correctly (e.g. search_web first, then read_page, then stop).\n" \
            "SEARCH INSTRUCTION: When the user asks to 'open the first result', DO NOT use click_element. You MUST read the 'url' from the search_web JSON results and use the navigate(url) tool to open it directly!\n" \
            "NOTEPAD INSTRUCTION: When the user asks you to type something in Notepad, you MUST first use keyboard_action('ctrl+n') to open a new tab in Notepad before typing. NEVER type into an existing saved file/tab. NEVER open Brave or any browser after completing a typing task unless the user explicitly requests it. After type_text() returns success, you MUST immediately output a final text reply (e.g. 'Done.') and stop calling any further tools.\n" \
            "YOUTUBE INSTRUCTION: To play or pause a video, you MUST use keyboard_action('k'). NEVER use go_back or Space! If the user asks to search for something ON YouTube, DO NOT use search_web! You MUST use the navigate tool with the URL https://www.youtube.com/results?search_query=... directly!"
        )
        
        messages.append({"role": "system", "content": strong_instruction})
        
        
        # Intelligent history retention:
        # Keep System Prompt [0]
        # Keep the most recent explicit User message (not a tool result)
        # Keep the last 6 messages
        
        if len(history) > 7:
            processed_history = [history[0]]
            
            # Find the most recent explicit user message
            last_explicit_user_msg = None
            for msg in reversed(history[1:-6]):
                if msg["role"] == "user":
                    if "function_responses" not in msg and not (isinstance(msg.get("content"), str) and msg["content"].startswith("[Tool Result")):
                        last_explicit_user_msg = msg
                        break
                        
            if last_explicit_user_msg:
                processed_history.append(last_explicit_user_msg)
                
            processed_history.extend(history[-6:])
        else:
            processed_history = history


        
        for msg in processed_history:
            role = "user" if msg["role"] == "user" else "assistant"
            
            if "function_calls" in msg:
                for fc in msg["function_calls"]:
                    messages.append({
                        "role": "assistant", 
                        "content": f"[Tool Call Executed: {fc['name']} with args {fc['args']}]"
                    })
                    
            if "function_responses" in msg:
                for fr in msg["function_responses"]:
                    import json
                    try:
                        res_str = json.dumps(fr['response'])
                    except Exception:
                        res_str = str(fr['response'])
                        
                    if len(res_str) > 3000:
                        res_str = res_str[:3000] + "... [TRUNCATED TO PREVENT GROQ TPM 413 CRASH]"
                        
                    messages.append({
                        "role": "user", 
                        "content": f"[Tool Result for {fr['name']}: {res_str}]"
                    })
                    
            if "content" in msg and msg["content"]:
                messages.append({"role": role, "content": msg["content"]})
        
        try:
            tools_list = registry.get_all_tools()
            groq_tools = [function_to_json_schema(t) for t in tools_list] if tools_list else None
            
            import time
            max_retries = 4
            for attempt in range(max_retries):
                try:
                    response = self.client.chat.completions.create(
                        model=self.model_name,
                        messages=messages,
                        tools=groq_tools,
                        tool_choice="auto" if groq_tools else "none",
                        temperature=0.0
                    )
                    break
                except Exception as e:
                    error_str = str(e)
                    if "429" in error_str and ("Rate limit" in error_str or "rate_limit_exceeded" in error_str):
                        match = re.search(r"Please try again in ([\d\.]+)s", error_str)
                        sleep_time = float(match.group(1)) if match else 5.0
                        sleep_time += 1.0 # Buffer
                        logger.warning(f"Groq Rate limit hit. Retrying in {sleep_time:.2f}s... (Attempt {attempt+1}/{max_retries})")
                        time.sleep(sleep_time)
                        if attempt == max_retries - 1:
                            raise e
                        continue
                        
                    if "failed_generation" in error_str and "<function=" in error_str:
                        match = re.search(r"<function=(\w+)(.*?)</function>", error_str)
                        if match:
                            tool_name = match.group(1)
                            tool_args_str = match.group(2).strip()
                            if tool_args_str.endswith(">"):
                                tool_args_str = tool_args_str[:-1]
                            try:
                                tool_args = json.loads(tool_args_str)
                                logger.info(f"Successfully rescued hallucinated tool call: {tool_name} with {tool_args}")
                                return {
                                    "type": "function_call",
                                    "name": tool_name,
                                    "args": tool_args
                                }
                            except Exception as parse_e:
                                logger.error(f"Could not rescue JSON: {parse_e}")
                    raise e
            
            message = response.choices[0].message
            
            if message.tool_calls:
                tc = message.tool_calls[0]
                try:
                    args = json.loads(tc.function.arguments) if tc.function.arguments else {}
                    if args is None:
                        args = {}
                except Exception:
                    args = {}
                return {
                    "type": "function_call",
                    "name": tc.function.name,
                    "args": args
                }
            else:
                # Fallback for LLaMA 8B text-leaked tool calls
                if message.content:
                    match = re.search(r"<(\w+)>(\{.*?\})</\1>", message.content, re.DOTALL)
                    if match:
                        tool_name = match.group(1)
                        tool_args_str = match.group(2).strip()
                        try:
                            tool_args = json.loads(tool_args_str)
                        except Exception:
                            try:
                                tool_args = ast.literal_eval(tool_args_str)
                            except Exception:
                                tool_args = {}
                        logger.info(f"Successfully rescued leaked text tool call: {tool_name}")
                        return {"type": "function_call", "name": tool_name, "args": tool_args}
                        
                    match3 = re.search(r"\[Tool Call Executed:\s+(\w+)(?:\s+with args\s+(\{.*?\}))?\]", message.content, re.DOTALL)
                    if match3:
                        tool_name = match3.group(1)
                        tool_args_str = match3.group(2).strip() if match3.group(2) else ''
                        try:
                            tool_args = json.loads(tool_args_str.replace("'", '"'))
                        except Exception:
                            try:
                                tool_args = ast.literal_eval(tool_args_str)
                            except Exception:
                                tool_args = {}
                        logger.info(f"Successfully rescued history-mimicked text tool call: {tool_name}")
                        return {"type": "function_call", "name": tool_name, "args": tool_args}
                        
                    match2 = re.search(r"<function=(\w+)[^>]*?>(\{.*?\})", message.content, re.DOTALL)
                    if match2:
                        tool_name = match2.group(1)
                        tool_args_str = match2.group(2).strip()
                        try:
                            tool_args = json.loads(tool_args_str)
                        except Exception:
                            try:
                                tool_args = ast.literal_eval(tool_args_str)
                            except Exception:
                                tool_args = {}
                        logger.info(f"Successfully rescued leaked text tool call (format 2): {tool_name}")
                        return {"type": "function_call", "name": tool_name, "args": tool_args}
                        
                return {"type": "text", "content": message.content}
                
        except Exception as e:
            error_str = str(e)
            logger.error(f"Error calling Groq: {error_str}")
            raise

def get_provider() -> AIProvider:
    if settings.ai_provider.lower() == "mock":
        return MockProvider()
    elif settings.ai_provider.lower() == "gemini":
        return GeminiProvider()
    elif settings.ai_provider.lower() == "groq":
        return GroqProvider()
    else:
        logger.warning(f"Unknown provider '{settings.ai_provider}', falling back to MockProvider.")
        return MockProvider()


