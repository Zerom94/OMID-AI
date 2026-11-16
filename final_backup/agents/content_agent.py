import httpx
from agents.base import BaseAgent, Task, Result

class ContentAgent(BaseAgent):
    name = "ContentAgent"
    display_name = "Content Writer"

    async def execute(self, task: Task) -> Result:
        self.log_event("working", {"agent": self.name, "status": "Writing high-quality content..."})
        
        prompt = (
            "You are an expert Content Writer, Copywriter, and SEO Specialist.\n"
            f"Task: {task.description}\n"
            "Write a highly engaging, professional, and well-structured content in Persian.\n"
            "Use appropriate formatting (Markdown) with headings, bullet points, and emojis if suitable for the platform.\n"
            "Do NOT output any conversational text outside of the requested content."
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
                
                self.log_event("chat", {"text": content})
                self.log_event("complete", {"agent": self.name, "status": "Done"})
                return Result(task_id=task.id, success=True, output="Content generated.")
        except Exception as e:
            return Result(task_id=task.id, success=False, output=str(e))
