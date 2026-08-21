with open('backend/tools/windows_apps.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
for line in lines:
    new_lines.append(line)
    if '"description": "Brave Browser"' in line:
        new_lines.append('        "args": ["--remote-debugging-port=9222"]\n')

with open('backend/tools/windows_apps.py', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)
print("Added args to Brave in windows_apps.py")
