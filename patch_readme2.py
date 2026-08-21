with open(r'README.md', 'r', encoding='utf-8') as f:
    readme = f.read()

new_section = '''
## Stage 7 - Computer Vision & Screen Understanding
JARVIS can now "see" the screen using the GroqVisionProvider and llama-3.2-11b-vision-preview!
- **Visual Targeting**: When deterministic automation fails, JARVIS can fallback to isual_click to visually locate UI elements and click them.
- **Active Window Detection**: Automatically detects the foreground window using the Windows API to restrict coordinate mapping and token usage to the relevant context.
- **Visual Verification**: JARVIS uses isual_verify to take a screenshot and confirm if an action (like opening a menu or navigating to a page) succeeded.
- **Privacy-First**: Screenshots are saved to temporary memory and aggressively deleted immediately after the Vision API processes them. JARVIS does NOT continuously record your screen; it only captures when requested.
'''

if 'llama-3.2-11b-vision-preview' not in readme:
    readme += new_section
    with open(r'README.md', 'w', encoding='utf-8') as f:
        f.write(readme)
    print("Added Stage 7 details to README.")
