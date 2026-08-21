import re as regex_module

with open('backend/provider.py', 'r', encoding='utf-8') as f:
    code = f.read()

if 'import re' not in code:
    code = 'import re\n' + code
    with open('backend/provider.py', 'w', encoding='utf-8') as f:
        f.write(code)
    print("Added import re to provider.py")
else:
    print("import re already exists, maybe inside a function?")
    # Check if it's at the top level
    if not code.startswith('import re\n'):
        code = 'import re\n' + code
        with open('backend/provider.py', 'w', encoding='utf-8') as f:
            f.write(code)
        print("Forced import re to the top of provider.py")
