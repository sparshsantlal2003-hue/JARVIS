import re

with open('backend/tools/windows_apps.py', 'r', encoding='utf-8') as f:
    code = f.read()

# 1. Update the registry entry for Brave
old_brave = '''    "brave": {
        "executable": r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe",
        "description": "Brave Browser"
    },'''
new_brave = '''    "brave": {
        "executable": r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe",
        "description": "Brave Browser",
        "args": ["--remote-debugging-port=9222"]
    },'''
code = code.replace(old_brave, new_brave)

# 2. Update the Popen call
old_popen = '''    try:
        logger.info(f"Launching application: {resolved_key} ({executable})")
        subprocess.Popen([executable], shell=False)
        time.sleep(1.5)'''
new_popen = '''    try:
        args = app_info.get("args", [])
        logger.info(f"Launching application: {resolved_key} ({executable}) with args {args}")
        subprocess.Popen([executable] + args, shell=False)
        time.sleep(1.5)'''
code = code.replace(old_popen, new_popen)

with open('backend/tools/windows_apps.py', 'w', encoding='utf-8') as f:
    f.write(code)

print("Updated windows_apps.py to launch Brave with debugging port.")
