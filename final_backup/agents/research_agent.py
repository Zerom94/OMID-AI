import httpx
import urllib.parse
from agents.base import BaseAgent, Task, Result

class ResearchAgent(BaseAgent):
    name = "ResearchAgent"
    display_name = "Research"

    async def execute(self, task: Task) -> Result:
        self.log_event("working", {"agent": self.name, "status": f"Searching GitHub..."})
        
        # جستجوی هدفمند برای پروژه‌های پایتون خالص (Streamlit)
        queries = [
            urllib.parse.quote(f"{task.description} streamlit language:python"),
            urllib.parse.quote("streamlit beautiful dashboard"),
            urllib.parse.quote("streamlit todo app")
        ]
        
        for query in queries:
            url = f"https://api.github.com/search/repositories?q={query}&sort=stars&order=desc&per_page=1"
            try:
                async with httpx.AsyncClient() as client:
                    resp = await client.get(url, headers={"Accept": "application/vnd.github.v3+json"}, timeout=15.0)
                    data = resp.json()
                    
                    if data.get("total_count", 0) > 0:
                        best_repo = data["items"][0]
                        repo_name = best_repo["full_name"]
                        repo_url = best_repo["html_url"]
                        description = best_repo["description"]
                        
                        self.log_event("chat", {"text": f"✅ محقق پیدا کرد: [{repo_name}]({repo_url})\nتوضیحات: {description}"})
                        return Result(task_id=task.id, success=True, output=f"Repo: {repo_name}\nURL: {repo_url}\nDescription: {description}")
            except Exception:
                continue
                
        self.log_event("chat", {"text": "⚠️ محقق در گیت‌هاب چیزی پیدا نکرد. از دانش داخلی برای ساخت Streamlit استفاده می‌کنم."})
        return Result(task_id=task.id, success=True, output="Use Streamlit best practices for a beautiful app.")
