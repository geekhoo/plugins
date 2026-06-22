import json


def load_json_file(path, issues, label):
    if not path.exists():
        issues.append(f"{label} is missing")
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        issues.append(f"{label} is not valid JSON: {exc}")
        return None
