import os
import glob

def clean_ufeff(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
        
    if '\ufeff' in content:
        content = content.replace('\ufeff', '')
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Cleaned \ufeff from {filepath}")

for root, _, files in os.walk('backend'):
    for file in files:
        if file.endswith('.py'):
            clean_ufeff(os.path.join(root, file))
