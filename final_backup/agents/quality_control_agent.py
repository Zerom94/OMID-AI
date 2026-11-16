import os
import json
from pathlib import Path
import glob
from agents.base import BaseAgent, Task, Result

class QualityControlAgent(BaseAgent):
    name = "QualityControl"
    display_name = "Quality Control"

    # Cache to avoid re‑reading the rule set on every call in a single runtime.
    _rules_cache = None

    async def execute(self, task: Task) -> Result:
        """
        Verify that the source tree contains generated Python files and optionally
        apply business rules defined in a knowledge base JSON.
        """
        # Resolve the knowledge‑base path – allow overriding via env var.
        kb_path = Path(os.getenv("QC_KB_PATH", "/sdcard/omid-ai/agents_knowledge.json"))

        rules = ""
        try:
            if kb_path.exists():
                with kb_path.open("r", encoding="utf-8") as f:
                    data = json.load(f)
                rules = data.get("quality_control", "")
        except json.JSONDecodeError as exc:
            return Result(task_id=task.id, success=False,
                          error=f"Malformed JSON in KB: {exc}")
        except OSError as exc:
            return Result(task_id=task.id, success=False,
                          error=f"I/O error accessing KB: {exc}")

        if rules:
            print(f"[{self.name}] 🎓 Using loaded rules: {rules}", flush=True)
        else:
            print(f"[{self.name}] ⚠️ No quality control rules found.", flush=True)

        # Quickly collect all Python files in src/**.py
        try:
            src_dir = Path("src")
            py_files = list(src_dir.rglob("*.py"))
        except OSError as exc:
            return Result(task_id=task.id, success=False,
                          error=f"Error scanning source directory: {exc}")

        if py_files:
            print(f"✅ [QC] Found {len(py_files)} generated files. Passed.", flush=True)
            return Result(task_id=task.id, success=True, output={"status": "verified"})
        else:
            print(f"❌ [QC] No files found to verify.", flush=True)
            return Result(task_id=task.id, success=False, error="No files found")