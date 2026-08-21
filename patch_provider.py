import sys

with open(r'backend\provider.py', 'r', encoding='utf-8') as f:
    code = f.read()

# 1. Add import
old_imports = '''import backend.tools.windows_apps  # Ensures tools are registered
import backend.tools.browser       # Ensures browser tools are registered'''
new_imports = '''import backend.tools.windows_apps  # Ensures tools are registered
import backend.tools.browser       # Ensures browser tools are registered
import backend.tools.vision_tools  # Ensures vision tools are registered'''
code = code.replace(old_imports, new_imports)

# 2. Add System Prompt instructions for Vision fallback
old_instruction = '''            "YOUTUBE INSTRUCTION: To play or pause a video, you MUST use keyboard_action('k'). NEVER use go_back or Space! If the user asks to search for something ON YouTube, DO NOT use search_web! You MUST use the navigate tool with the URL https://www.youtube.com/results?search_query=... directly!"'''
new_instruction = '''            "YOUTUBE INSTRUCTION: To play or pause a video, you MUST use keyboard_action('k'). NEVER use go_back or Space! If the user asks to search for something ON YouTube, DO NOT use search_web! You MUST use the navigate tool with the URL https://www.youtube.com/results?search_query=... directly!\\n" \\
            "VISION FALLBACK INSTRUCTION: Use deterministic tools (like launch_application, Playwright browser tools) FIRST. If deterministic tools fail, or if you need to verify an ambiguous visual state, use visual_click to click elements, describe_screen to see what's visible, and visual_verify to confirm if an action succeeded."'''
code = code.replace(old_instruction, new_instruction)

with open(r'backend\provider.py', 'w', encoding='utf-8') as f:
    f.write(code)

print("Updated provider.py with vision imports and instructions.")
