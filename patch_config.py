with open(r'backend\config.py', 'r', encoding='utf-8') as f:
    code = f.read()

new_config = '''    # Stage 7 - Vision
    vision_enabled: bool = True
    vision_min_confidence: float = 0.80
    vision_max_retries: int = 2
    vision_model: str = "llama-3.2-11b-vision-preview"

    class Config:'''

code = code.replace('    class Config:', new_config)

with open(r'backend\config.py', 'w', encoding='utf-8') as f:
    f.write(code)

print("Updated config.py")
