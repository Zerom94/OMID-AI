import os
import httpx
import re
from agents.base import BaseAgent, Task, Result

class DeveloperAgent(BaseAgent):
    name = "Developer"
    display_name = "Developer"

    async def execute(self, task: Task) -> Result:
        self.log_event("working", {"agent": self.name, "status": "Writing Pro Python App..."})
        
        prompt = (
            "You are a Principal Full-Stack Engineer and a World-Class UI/UX Designer.\n"
            f"Task: {task.description}\n"
            "Build an EXTREMELY ADVANCED, production-ready Streamlit web application.\n"
            "CRITICAL REQUIREMENTS:\n"
            "1. Tech Stack: Pure Python (Streamlit). Do NOT use Flask or Django.\n"
            "2. Modern UI: Use `st.markdown` to inject advanced custom CSS for a 'Cyberpunk/Neon' or 'Premium Glassmorphism' look.\n"
            "3. Latest Features: Use `st.rerun()` (NOT experimental_rerun). Use `st.toast()` for success messages. "
            "For modals, you MUST use the decorator syntax: `@st.dialog(\"Title\")` above a function. Do NOT call `st.dialog` as a context manager.\n"
            "4. Data Persistence: Use Python's built-in `sqlite3` or `json` to save user data to a local file (e.g., `tasks.json`). The app must NOT lose data on refresh.\n"
            "5. Advanced Features: Add filtering (All, Active, Completed), a progress bar (`st.progress`), and a clean, modern navigation sidebar (`st.sidebar`).\n"
            "6. No Errors: Every st.button MUST have a unique label. Do NOT use empty labels.\n"
            "7. Output ONLY ONE file named 'app.py'.\n"
            "Format exactly like this:\n"
            "### FILE: app.py\n"
            "```python\n"
            "import streamlit as st\n"
            "# code here\n"
            "```\n"
            "Do NOT output any conversational text."
        )
        
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    "http://127.0.0.1:5001/v1/chat/completions",
                    json={"model": "openai/gpt-oss-120b", "messages": [{"role": "user", "content": prompt}]},
                    timeout=120.0
                )
                data = resp.json()
                content = data["choices"][0]["message"]["content"]
                
                pattern = r'### FILE:\s*([^\n]+)\n```[^\n]*\n(.*?)```'
                matches = re.findall(pattern, content, re.DOTALL)
                
                if not matches:
                    return Result(task_id=task.id, success=False, output="Failed to parse files.")
                    
                project_dir = f"src/pyapp_{os.urandom(2).hex()}"
                os.makedirs(project_dir, exist_ok=True)
                
                display_code = ""

                for filename, code_content in matches:
                    filename = filename.strip()
                    code_content = code_content.strip()
                    
                    filepath = os.path.join(project_dir, filename)
                    with open(filepath, "w", encoding="utf-8") as file:
                        file.write(code_content)
                    
                    display_code += f"# === {filename} ===\n{code_content}\n\n"
                
                self.log_event("code_generated", {
                    "filename": project_dir, 
                    "code": display_code.strip(),
                    "is_html": False,
                    "html_content": ""
                })
                
                return Result(task_id=task.id, success=True, output="Pure Python App generated.")
        except Exception as e:
            return Result(task_id=task.id, success=False, output=str(e))
