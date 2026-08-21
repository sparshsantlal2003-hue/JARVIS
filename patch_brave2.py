import re

with open('backend/tools/windows_apps.py', 'r', encoding='utf-8') as f:
    code = f.read()

new_brave = '''    "brave": {
        "executable": r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe",
        "description": "Brave Browser",
        "args": ["--remote-debugging-port=9222"]
    },'''

code = re.sub(
    r'"brave":\s*\{\s*"executable":\s*r"C:\\Program Files\\BraveSoftware\\Brave-Browser\\Application\\brave\.exe",\s*"description":\s*"Brave Browser"\s*\},',
    new_brave,
    code
)

with open('backend/tools/windows_apps.py', 'w', encoding='utf-8') as f:
    f.write(code)

print("Updated windows_apps.py brave registry with regex.")
