import re

with open('backend/tray.py', 'r', encoding='utf-8') as f:
    code = f.read()

code = code.replace(r'\"\"\"Starts the system tray icon in a daemon thread.\"\"\"', '\"\"\"Starts the system tray icon in a daemon thread.\"\"\"')

with open('backend/tray.py', 'w', encoding='utf-8') as f:
    f.write(code)

print("tray.py fixed.")
