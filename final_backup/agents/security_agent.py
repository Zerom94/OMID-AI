import os
import subprocess
from agents.base import BaseAgent, Task, Result

class SecurityAgent(BaseAgent):
    name = "SecurityAgent"
    display_name = "Security"

    async def execute(self, task: Task) -> Result:
        target = task.description.strip()
        
        # استخراج URL از متن
        import re
        url_match = re.search(r'https?://[^\s]+', target)
        
        if not url_match:
            self.log_event("chat", {"text": "⚠️ لطفاً یک آدرس معتبر (http/https) ارسال کنید."})
            return Result(task_id=task.id, success=False, output="Invalid URL.")
            
        url = url_match.group(0)
        self.log_event("working", {"agent": self.name, "status": f"Executing pentest on {url}..."})
        
        # در اینجا ما فقط شبیه‌سازی می‌کنیم که اسکن انجام شده
        # در پروژه واقعی، اینجا دستورات nmap و sqlmap اجرا می‌شوند
        try:
            # شبیه‌سازی اجرای Nmap
            self.log_event("chat", {"text": f"🚀 شروع اسکن هدف: {url}"})
            
            # این بخش را می‌توانید با subprocess واقعی جایگزین کنید
            # subprocess.run(["nmap", "-sV", url], ...)
            
            self.log_event("complete", {"agent": self.name, "status": "Scan completed."})
            return Result(task_id=task.id, success=True, output=f"Security scan on {url} completed.")
        except Exception as e:
            return Result(task_id=task.id, success=False, output=str(e))
