import os
import httpx
import re
import json
from agents.base import BaseAgent, Task, Result

class DeveloperAgent(BaseAgent):
    name = "Developer"
    display_name = "Developer"

    async def execute(self, task: Task) -> Result:
        self.log_event("working", {"agent": self.name, "status": "Writing Streamlit App..."})
        
        tick = chr(96) * 3
        prompt = "You are an expert Python Developer specializing in Streamlit and UI design.\n"
        prompt += f"Task: {task.description}\n\n"
        prompt += "CRITICAL STREAMLIT RULES:\n"
        prompt += "1. You MUST use ONLY Streamlit. NEVER use Flask or Django.\n"
        prompt += "2. Output ONLY ONE file named 'app.py'.\n"
        prompt += "3. NEVER use `css_class` in `st.button` or any other widget. It causes errors.\n"
        prompt += "4. To style buttons, use `type=\"primary\"` or inject custom CSS via `st.markdown('<style>...</style>', unsafe_allow_html=True)`.\n"
        prompt += "5. Create a breathtaking Dark Mode / Glassmorphism UI using custom CSS injected with `st.markdown`.\n"
        prompt += "6. Format exactly like this:\n"
        prompt += "PROJECT_NAME: [Your_Project_Name_Here]\n"
        prompt += f"### FILE: app.py\n{tick}python\nimport streamlit as st\n# code here\n{tick}\n"
        prompt += "7. Do NOT output any conversational text outside of this block.\n"
        
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

                counter_file = "/sdcard/omid-ai/project_counter.json"
                counter = 1001
                if os.path.exists(counter_file):
                    try:
                        with open(counter_file, "r") as f:
                            data_c = json.load(f)
                            counter = data_c.get("counter", 1001)
                    except Exception:
                        pass
                
                with open(counter_file, "w") as f:
                    json.dump({"counter": counter + 1}, f)

                project_dir = f"src/{safe_name}_{counter}"
                os.makedirs(project_dir, exist_ok=True)
                
                backtick = chr(96)
                triple_backtick = backtick * 3
                pattern = r'### FILE:\s*([^\n]+)\n' + triple_backtick + r'[^\n]*\n(.*?)' + triple_backtick
                
                matches = re.findall(pattern, content, re.DOTALL)
                
                if not matches:
                    return Result(task_id=task.id, success=False, output="Failed to parse files.")
                    
                display_code = ""

                for filename, code_content in matches:
                    filename = filename.strip()
                    code_content = code_content.strip()
                    
                    # 🟢 فیلتر خودکار: حذف css_class از کدهای تولید شده اگر وجود داشت
                    code_content = re.sub(r',\s*css_class\s*=\s*"[^"]*"', '', code_content)
                    code_content = re.sub(r',\s*css_class\s*=\s*\'[^\']*\'', '', code_content)
                    
                    filepath = os.path.join(project_dir, filename)
                    with open(filepath, "w", encoding="utf-8") as file:
                        file.write(code_content)
                    
                    display_code += f"# === {filename} ===\n{code_content}\n\n"
                
                self.log_event("code_generated", {
                    "filename": f"{safe_name}_{counter}/app.py", 
                    "file_path": f"{project_dir}/app.py",
                    "code": display_code.strip(),
                    "is_html": False,
                    "html_content": ""
                })
                
                return Result(task_id=task.id, success=True, output="Code generated.")
        except Exception as e:
            return Result(task_id=task.id, success=False, output=str(e))
