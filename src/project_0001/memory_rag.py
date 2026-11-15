import json, os

PREF_PATH = os.path.join(os.path.dirname(__file__), "memory_rag.json")

def save_user_preference(preference: dict) -> None:
    """Save a flat dict of user preferences to memory_rag.json."""
    if not isinstance(preference, dict):
        raise ValueError("Preference must be a dict")
    with open(PREF_PATH, "w", encoding="utf-8") as f:
        json.dump(preference, f, ensure_ascii=False, indent=2)

def _load_user_preference() -> dict:
    """Load stored preferences; return {} if file missing or invalid."""
    if not os.path.isfile(PREF_PATH):
        return {}
    try:
        with open(PREF_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}

def enrich_system_prompt(base_prompt: str) -> str:
    """Inject stored user info into the system prompt."""
    prefs = _load_user_preference()
    if prefs:
        info = ", ".join(f"{k}: {v}" for k, v in prefs.items())
        return f"{base_prompt}
User context: {info}"
    return base_prompt

# Example integration point (replace with your actual call site)
# def build_prompt(...):
#     sys_prompt = enrich_system_prompt(original_system_prompt)
#     ...
