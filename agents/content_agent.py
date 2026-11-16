"""OMID AI - Content Creation Agent"""
import os
import json
import httpx
import re
from agents.base import BaseAgent, Task, Result
from core.db import get_db

class ContentAgent(BaseAgent):
    name = "ContentAgent"
    display_name = "Content Creator"

    async def execute(self, task: Task) -> Result:
        self.log_event("working", {"agent": self.name, "status": "Creating content..."})
        
        prompt = f"""You are a professional content creator and copywriter.
Task: {task.description}
Create high-quality content in Persian that includes:
1. Engaging headlines
2. Persuasive body text
3. Clear call-to-action
4. SEO optimization tips
Format your response with clear sections for different content types.
"""
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    "http://127.0.0.1:5001/v1/chat/completions",
                    json={"model": "openai/gpt-oss-120b", "messages": [{"role": "user", "content": prompt}]},
                    timeout=90.0
                )
                data = resp.json()
                if "choices" not in data:
                    return Result(task_id=task.id, success=False, output="Error communicating with Router.")
                content_result = data["choices"][0]["message"]["content"]

            db = get_db()
            db.add_message("user", f"[Content creation: {task.description}]")
            db.add_message("assistant", content_result)
            
            self.log_event("content_created", {"task": task.description})
            return Result(task_id=task.id, success=True, output=content_result)
        except Exception as e:
            return Result(task_id=task.id, success=False, output=str(e))
