with open('backend/tools/windows_apps.py', 'r', encoding='utf-8') as f:
    code = f.read()

code = code.replace('"description": "Brave Browser"\n        "args":', '"description": "Brave Browser",\n        "args":')

with open('backend/tools/windows_apps.py', 'w', encoding='utf-8') as f:
    f.write(code)

print("Fixed missing comma in windows_apps.py")
