import os
import json

mapping = {f: f for f in os.listdir() if os.path.isfile(f)}
with open("mapping.json", "w", encoding="utf-8") as f:
    json.dump(mapping, f, indent=4, ensure_ascii=False)
