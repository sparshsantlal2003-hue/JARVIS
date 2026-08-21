import codecs
import os
import glob

def strip_bom(filepath):
    with open(filepath, 'rb') as f:
        content = f.read()
    if content.startswith(codecs.BOM_UTF8):
        content = content[len(codecs.BOM_UTF8):]
        with open(filepath, 'wb') as f:
            f.write(content)
        print(f"Stripped BOM from {filepath}")

for root, _, files in os.walk('backend'):
    for file in files:
        if file.endswith('.py'):
            strip_bom(os.path.join(root, file))
            
for file in glob.glob('tests/*.py'):
    strip_bom(file)
