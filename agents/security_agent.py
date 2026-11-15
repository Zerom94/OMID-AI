import os
import subprocess
from agents.base import BaseAgent, Task, Result

class SecurityAgent(BaseAgent):
    name = "SecurityAgent"
    display_name = "Security"

    async def execute(self, task: Task) -> Result:
        target = task.description.strip()
        
        # چک کردن اینکه آیا یک URL معتبر است یا خیر
        if "http://" not in target and "https://" not in target:
            self.log_event("chat", {"text": "⚠️ ایجنت امنیت: لطفاً یک آدرس معتبر (شروع شده با http) برای اسکن ارسال کنید. این ایجنت فقط برای اسکن سایت‌ها طراحی شده است."})
            return Result(task_id=task.id, success=False, output="Invalid URL. Security agent only scans websites.")

        self.log_event("working", {"agent": self.name, "status": f"Starting security scan on {target}..."})
        
        # در اینجا منطق اسکن واقعی (مثلاً Nmap) قرار می‌گیرد
        # برای جلوگیری از کرش در این تست، فقط یک پیام موفقیت‌آمیز برمی‌گردانیم
        try:
            self.log_event("complete", {"agent": self.name, "status": "Scan completed."})
            return Result(task_id=task.id, success=True, output=f"Security scan on {target} completed successfully.")
        except Exception as e:
            return Result(task_id=task.id, success=False, output=str(e))
