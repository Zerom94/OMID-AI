import os
import httpx
import re
import json
from agents.base import BaseAgent, Task, Result
from core.db import get_db

class DeveloperAgent(BaseAgent):
    name = "Developer"
    display_name = "Developer"

    async def execute(self, task: Task) -> Result:
        self.log_event("working", {"agent": self.name, "status": "Writing Python Script..."})
        
        tick = chr(96) * 3
        prompt = f" You are an expert Python Developer.\nTask: {task.description}\n\nCRITICAL REQUIREMENTS:\n1. Output ONLY raw Python scripts (NO web frameworks like Streamlit/Flask/Django).\n2. Include only standard libraries or commonly used third-party libs.\n3. Format exactly like this:\nPROJECT_NAME: [Your_Project_Name]\n### FILE: script.py\n{tick}python\n# Your code here\n{tick}\n4. Do NOT output any conversational text outside of this block.\n5. Make the code production-ready with error handling and logging.\n"
        
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    "http://127.0.0.1:5001/v1/chat/completions",
                    json={"model": "openai/gpt-oss-120b", "messages": [{"role": "user", "content": prompt}]},
                    timeout=120.0
                )
                data = resp.json()
                content = data["choices"][0]["message"]["content"]

                name_match = re.search(r'PROJECT_NAME:\s*([^\n]+)', content)
                if name_match:
                    safe_name = re.sub(r'[^a-zA-Z0-9_]', '', name_match.group(1).strip().replace(" ", "_"))
                else:
                    safe_name = "Project"

                db = get_db()
                # اصلاح باگ: اول آی‌دی رو می‌گیریم، بعد مسیر رو می‌سازیم
                project_id = db.reserve_project(safe_name, "temp")
                project_dir = f"src/{safe_name}_{project_id}"
                os.makedirs(project_dir, exist_ok=True)

                triple_bk = chr(96) * 3
                pattern = r'### FILE:\s*([^\n]+)\n' + triple_bk + r'[^\n]*\n(.*?)' + triple_bk
                matches = re.findall(pattern, content, re.DOTALL)

                if not matches:
                    return Result(task_id=task.id, success=False, output="Failed to parse files.")

                display_code = ""
                for filename, code_content in matches:
                    filename = filename.strip()
                    code_content = code_content.strip()
                    filepath = os.path.join(project_dir, filename)
                    with open(filepath, "w", encoding="utf-8") as file:
                        file.write(code_content)
                    display_code += f"# === {filename} ===\n{code_content}\n\n"

                self.log_event("code_generated", {
                    "filename": f"{safe_name}_{project_id}/script.py",
                    "file_path": f"{project_dir}/script.py",
                    "code": display_code.strip(),
                    "is_html": False,
                    "html_content": ""
                })
                return Result(task_id=task.id, success=True, output="Code generated.")
        except Exception as e:
            return Result(task_id=task.id, success=False, output=str(e))
