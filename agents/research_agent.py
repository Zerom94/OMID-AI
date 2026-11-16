"""OMID AI - Research Agent"""
import os
import json
import httpx
import re
from agents.base import BaseAgent, Task, Result
from core.db import get_db

class ResearchAgent(BaseAgent):
    name = "ResearchAgent"
    display_name = "Researcher"

    async def execute(self, task: Task) -> Result:
        self.log_event("working", {"agent": self.name, "status": "Searching for information..."})
        query = task.description
        
        prompt = f"""You are an expert research assistant.
Search query: {query}
Provide comprehensive, accurate information in Persian. Include:
1. Key findings
2. Relevant details
3. Sources if available
4. Recent developments
Format your response clearly with sections.
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
                research_result = data["choices"][0]["message"]["content"]

            db = get_db()
            db.add_message("user", f"[Research: {query}]")
            db.add_message("assistant", research_result)
            
            self.log_event("research_complete", {"query": query})
            return Result(task_id=task.id, success=True, output=research_result)
        except Exception as e:
            return Result(task_id=task.id, success=False, output=str(e))
