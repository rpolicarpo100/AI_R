
import json, os
from pathlib import Path

TEMPLATES_DIR = Path(__file__).parent

def load_templates():
    templates = {}
    for file in TEMPLATES_DIR.glob("*.json"):
        try:
            with open(file) as f:
                data = json.load(f)
                tid = file.stem
                templates[tid] = data
        except Exception as e:
            print(f"[TEMPLATES] Failed load {file}: {e}")
    return templates

TEMPLATES = load_templates()

def get_template(template_id: str):
    return TEMPLATES.get(template_id)

def list_templates():
    return [
        {
            "template_id": tid,
            "name": t["name"],
            "description": t["description"],
            "type": t["type"],
            "language": t["language"],
            "framework": t["framework"],
            "tags": t["tags"],
            "file_count": len(t["files"]),
            "files": list(t["files"].keys())
        }
        for tid, t in TEMPLATES.items()
    ]
