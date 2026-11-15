import os
import httpx
import json
import re
import subprocess
from core.auto_git import push_to_github
from agents.base import BaseAgent, Task, Result

class DeveloperAgent(BaseAgent):
    name = "Developer"
    display_name = "Developer"

    async def execute(self, task: Task) -> Result:
        self.log_event("working", {"agent": self.name, "status": "Writing code..."})
        
        prompt = f"""You are an expert Python developer. 
Task: {task.description}
Output your response ONLY as a JSON object with this exact structure:
{{"files": [{{"name": "main.py", "content": "print('hello')"}}]}}
Do NOT include markdown formatting like ```json.
"""
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    "http://127.0.0.1:5001/v1/chat/completions",
                    json={"model": "openai/gpt-oss-120b", "messages": [{"role": "user", "content": prompt}]},
                    timeout=120.0
                )
                data = resp.json()
                content = data["choices"][0]["message"]["content"]
                
                # Extract JSON safely
                match = re.search(r'\{.*\}', content, re.DOTALL)
                if match:
                    parsed = json.loads(match.group(0))
                    files = parsed.get("files", [])
                    
                    project_dir = f"src/project_{os.urandom(2).hex()}"
                    os.makedirs(project_dir, exist_ok=True)
                    
                    execution_output = ""
                    
                    for f in files:
                        filepath = os.path.join(project_dir, f["name"])
                        with open(filepath, "w", encoding="utf-8") as file:
                            file.write(f["content"])
                        
                        # اگر فایل پایتون بود، اجرا کن (Sandbox)
                        if f["name"].endswith(".py"):
                            self.log_event("working", {"agent": self.name, "status": f"Running {f['name']}..."})
                            try:
                                result = subprocess.run(
                                    ["python3", filepath],
                                    capture_output=True,
                                    text=True,
                                    timeout=15
                                )
                                if result.returncode == 0:
                                    execution_output += f"\n✅ Output of {f['name']}:\n{result.stdout}"
                                else:
                                    execution_output += f"\n❌ Error in {f['name']}:\n{result.stderr}"
                            except subprocess.TimeoutExpired:
                                execution_output += f"\n⚠️ Timeout: {f['name']} took too long."
                            except Exception as e:
                                execution_output += f"\n⚠️ Execution failed: {str(e)}"
                    
                    # نمایش نتیجه در داشبورد
                    self.log_event("chat", {"text": f"اجرای کد:\n{execution_output}"})
                    self.log_event("code_generated", {"filename": project_dir, "code": content})
                    git_result = await push_to_github(f"Auto-commit: {task.description}")
                    self.log_event("chat", {"text": git_result})
                    
                    return Result(task_id=task.id, success=True, output=execution_output)
                else:
                    return Result(task_id=task.id, success=False, output="Failed to parse JSON")
        except Exception as e:
            return Result(task_id=task.id, success=False, output=str(e))
