import re

with open('backend/agent.py', 'r', encoding='utf-8') as f:
    code = f.read()

old_except = '''                except Exception as e:
                    error_str = str(e)
                    if "tool_use_failed" in error_str or ("invalid_request_error" in error_str and "model_not_found" not in error_str):
                        logger.warning(f"AI generated malformed tool call. Prompting retry. Error: {error_str}")
                        self.history.append({
                            "role": "user",
                            "content": "SYSTEM ERROR: You generated a malformed tool call syntax. Please try again, and ensure you use correct formatting."
                        })
                        continue
                    raise e'''

new_except = '''                except Exception as e:
                    error_str = str(e)
                    # Do NOT retry on authentication/API key errors!
                    if "invalid_api_key" in error_str or "401" in error_str:
                        logger.error(f"Authentication Error: {error_str}")
                        return "JARVIS: Critical Error - My API key is invalid or missing. Please check your .env file."
                        
                    if "tool_use_failed" in error_str or ("invalid_request_error" in error_str and "model_not_found" not in error_str):
                        logger.warning(f"AI generated malformed tool call. Prompting retry. Error: {error_str}")
                        self.history.append({
                            "role": "user",
                            "content": "SYSTEM ERROR: You generated a malformed tool call syntax. Please try again, and ensure you use correct formatting."
                        })
                        continue
                    raise e'''

code = code.replace(old_except, new_except)

with open('backend/agent.py', 'w', encoding='utf-8') as f:
    f.write(code)
print("agent.py fixed to handle 401 errors correctly.")
