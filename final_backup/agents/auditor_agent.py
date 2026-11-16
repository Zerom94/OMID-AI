import httpx
from agents.base import BaseAgent, Task, Result

class AuditorAgent(BaseAgent):
    name = "Auditor"
    display_name = "Auditor"

    async def execute(self, task: Task) -> Result:
        code_to_check = task.description
        print(f"[Auditor] 🔎 Auditing downloaded code...", flush=True)
        
        prompt = f"""
        You are an expert Cybersecurity Auditor. Analyze the following Python code.
        Check for: 1. Syntax Errors. 2. Missing imports. 3. Security risks (malware, data theft).
        
        Code:
        {code_to_check[:2000]}
        
        Output a short report in Persian. Start with "✅ SAFE" if it's generally safe, or "❌ DANGEROUS" if it's malicious/broken.
        """
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post("http://127.0.0.1:5001/v1/chat/completions", json={
                    "model": "openai/gpt-oss-120b", "messages": [{"role": "user", "content": prompt}]
                }, timeout=60.0)
                report = resp.json()['choices'][0]['message']['content']
                self.log_event("chat", {"text": f"🛡️ گزارش حسابرس:\n\n{report}"})
                return Result(task_id=task.id, success=True, output=report)
        except Exception as e:
            return Result(task_id=task.id, success=False, output=str(e))
