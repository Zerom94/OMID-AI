import json, threading, os
from typing import Any, Dict

_lock = threading.Lock()
_PREF_PATH = "memory_rag.json"

def _load_preferences() -> Dict[str, Any]:
    """Load stored user preferences safely.
    Returns an empty dict if the file does not exist or is malformed.
    """
    if not os.path.isfile(_PREF_PATH):
        return {}
    try:
        with open(_PREF_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return {}

def save_user_preference(prefs: Dict[str, Any]) -> None:
    """Thread‑safe update of user preferences stored in ``memory_rag.json``.
    ``prefs`` is merged into existing data without overwriting unrelated keys.
    """
    with _lock:
        data = _load_preferences()
        data.update(prefs)
        try:
            with open(_PREF_PATH, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except OSError:
            pass

def generate_response(user_messages: list) -> str:
    """Create a response, injecting stored preferences into the system prompt.
    ``user_messages`` is a list of dicts as expected by the LLM client.
    """
    prefs = _load_preferences()
    context_parts = []
    if "name" in prefs:
        context_parts.append(f"User's name is {prefs['name']}")
    if "job" in prefs:
        context_parts.append(f"works as a {prefs['job']}")
    if "interests" in prefs:
        context_parts.append(f"likes {prefs['interests']}")
    context = ", ".join(context_parts)
    system_prompt = f"You are a helpful assistant. {context}" if context else "You are a helpful assistant."
    # Placeholder for actual LLM call
    return f"[System Prompt]
{system_prompt}
[User Messages]
{user_messages}"

# Unit tests
import unittest

class TestMemoryRAG(unittest.TestCase):
    def setUp(self):
        # Ensure a clean state
        if os.path.isfile(_PREF_PATH):
            os.remove(_PREF_PATH)
    def test_save_and_load(self):
        save_user_preference({"name": "Alice", "job": "engineer"})
        self.assertEqual(_load_preferences().get("name"), "Alice")
        save_user_preference({"interests": "hiking"})
        prefs = _load_preferences()
        self.assertEqual(prefs.get("job"), "engineer")
        self.assertEqual(prefs.get("interests"), "hiking")
    def test_context_injection(self):
        save_user_preference({"name": "Bob", "job": "designer", "interests": "painting"})
        resp = generate_response([{"role": "user", "content": "Hello"}])
        self.assertIn("User's name is Bob", resp)
        self.assertIn("works as a designer", resp)
        self.assertIn("likes painting", resp)

if __name__ == "__main__":
    unittest.main()
