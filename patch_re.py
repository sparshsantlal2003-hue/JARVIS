import sys

with open('backend/provider.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
for line in lines:
    if line.strip() == 'import re':
        # Don't add it if it's deeply indented (i.e. inside a function where it ruins scope)
        if line.startswith('                        import re'):
            continue
    new_lines.append(line)

with open('backend/provider.py', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)
print("Removed local import re")
