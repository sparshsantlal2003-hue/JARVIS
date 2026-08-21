import re
import os

with open('backend/startup.py', 'r', encoding='utf-8') as f:
    code = f.read()

# Replace get_startup_command
old_cmd = '''def get_startup_command() -> str:
    \"\"\"Returns the command used to launch JARVIS in background mode at startup.\"\"\"
    pythonw = get_pythonw_path()
    project_root = Path(__file__).parent.parent.absolute()
    return f'"{pythonw}" -m backend.main --background\''''

new_cmd = '''def get_startup_command() -> str:
    \"\"\"Returns the command used to launch JARVIS in background mode at startup.\"\"\"
    pythonw = get_pythonw_path()
    project_root = Path(__file__).parent.parent.absolute()
    run_script = project_root / 'run_jarvis.pyw'
    return f'"{pythonw}" "{run_script}"\''''

if old_cmd in code:
    code = code.replace(old_cmd, new_cmd)
else:
    # Try with regex just in case
    code = re.sub(r'def get_startup_command.*?return f.*?\n', new_cmd + '\n', code, flags=re.DOTALL)

with open('backend/startup.py', 'w', encoding='utf-8') as f:
    f.write(code)

print("Startup logic updated to use run_jarvis.pyw")
