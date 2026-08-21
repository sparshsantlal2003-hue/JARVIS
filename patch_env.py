with open(r'.env.example', 'a', encoding='utf-8') as f:
    f.write('\n# Stage 7 - Vision\n')
    f.write('VISION_ENABLED=True\n')
    f.write('VISION_MIN_CONFIDENCE=0.80\n')
    f.write('VISION_MAX_RETRIES=2\n')
    f.write('VISION_MODEL=llama-3.2-11b-vision-preview\n')

print("Updated .env.example")
