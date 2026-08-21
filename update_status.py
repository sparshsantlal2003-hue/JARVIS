import json

with open(r'.github\jarvis_status.json', 'r', encoding='utf-8-sig') as f:
    data = json.load(f)

data['Stage 7'] = 'complete'

with open(r'.github\jarvis_status.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=4)

print("Updated jarvis_status.json")
