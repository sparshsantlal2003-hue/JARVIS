import codecs

with open('backend/provider.py', 'rb') as f:
    content = f.read()

# Strip UTF-8 BOM if present
if content.startswith(codecs.BOM_UTF8):
    content = content[len(codecs.BOM_UTF8):]

with open('backend/provider.py', 'wb') as f:
    f.write(content)

print("BOM removed from provider.py")
