import os, json

with open("mapping.json", "r", encoding="utf-8") as f:
    for old_name, new_name in json.load(f).items():
        
        if old_name != new_name and os.path.exists(old_name):
            os.rename(old_name, new_name)
