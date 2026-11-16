import os
import json
import glob
import httpx
import re
import asyncio
from json_repair import loads as repair_json
from agents.base import BaseAgent, Task, Result

class DeveloperAgent(BaseAgent):
    name = "Developer"
    display_name = "Software Developer"

    async def execute(self, task: Task) -> Result:
        os.makedirs("src", exist_ok=True)
        max_idx = max([int(os.path.basename(d).replace("project_", "")) for d in glob.glob("src/project_*") if os.path.isdir(d)] + [0])
        project_dir = f"src/project_{max_idx + 1:04d}"
        os.makedirs(project_dir, exist_ok=True)

        prompt = f"""You are an expert Python developer.
Your task is EXACTLY: {task.description}

CRITICAL INSTRUCTIONS:
1. Output ONLY valid JSON. No markdown, no explanations.
2. The JSON MUST have this exact structure: {{"files": [{{"name": "main.py", "content": "python code here"}}]}}
3. Keep the code SHORT and CONCISE (under 50 lines).
4. Ensure all newlines are escaped as \\n.
"""

        # تلاش مجدد (تا ۳ بار)
        for attempt in range(3):
            print(f"[Developer] Requesting code (Attempt {attempt+1}/3)...", flush=True)
            
            raw = await self.call_self(prompt)
            print(f"[Developer] RAW RESPONSE (First 50 chars): {raw[:50]}...", flush=True)

            # بررسی خطای شبکه (پیام پیش‌فرض روتر)
            if raw.strip() == "I am processing your request. Please try again." or not raw.strip():
                print(f"[Developer] Network error detected. Waiting 5 seconds...", flush=True)
                await asyncio.sleep(5)
                continue

            # تلاش برای پیدا کردن JSON
            match = re.search(r'\{.*\}', raw, re.DOTALL)
            if match:
                try:
                    data = repair_json(match.group(0))
                    files = data.get("files", [])
                    if files:
                        return self._save_files(project_dir, files, task)
                except Exception as e:
                    print(f"[Developer] JSON Repair failed: {e}", flush=True)

            # اگر JSON نبود، تلاش برای استخراج از مارک‌داون
            code_match = re.search(r'```(?:python)?\n(.*?)\n```', raw, re.DOTALL)
            if code_match:
                extracted_code = code_match.group(1).strip()
                files = [{"name": "main.py", "content": extracted_code}]
                return self._save_files(project_dir, files, task)
            
            await asyncio.sleep(2)

        return Result(task_id=task.id, success=False, output="All attempts failed due to network/rate limits.")

    def _save_files(self, project_dir, files, task):
        try:
            final_main_code = "# No code generated."
            for f in files:
                fname = f.get("name", "main.py")
                fcontent = f.get("content", "")
                fcontent = fcontent.replace('\\n', '\n').replace('\\"', '"')
                
                file_path = os.path.join(project_dir, fname)
                dir_path = os.path.dirname(file_path)
                if dir_path:
                    os.makedirs(dir_path, exist_ok=True)
                
                with open(file_path, "w", encoding="utf-8") as file:
                    file.write(fcontent)
                    
                if fname == "main.py":
                    final_main_code = fcontent
                    
            print(f"[Developer] ✅ Files saved in {project_dir}.", flush=True)
            self.log_event("code_generated", {"filename": f"{project_dir}/main.py", "code": final_main_code})
            return Result(task_id=task.id, success=True)
        except Exception as e:
            return Result(task_id=task.id, success=False, output=str(e))

    async def call_self(self, prompt: str) -> str:
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    "http://localhost:5001/v1/chat/completions",
                    json={"model": "openai/gpt-oss-120b", "messages": [{"role": "user", "content": prompt}]},
                    timeout=120.0
                )
                data = resp.json()
                if 'choices' in data: 
                    return data['choices'][0]['message']['content']
        except Exception as e:
            print(f"Error connecting to router: {e}", flush=True)
        return "I am processing your request"
