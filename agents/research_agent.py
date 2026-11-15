import httpx
import urllib.parse
import os
import json
from agents.base import BaseAgent, Task, Result

class ResearchAgent(BaseAgent):
    name = "Research"
    display_name = "Research"

    async def execute(self, task: Task) -> Result:
        # ۱. خواندن قوانین یادگرفته شده
        kb_path = "/sdcard/omid-ai/agents_knowledge.json"
        if os.path.exists(kb_path):
            try:
                with open(kb_path, "r", encoding="utf-8") as f:
                    rules = json.load(f).get("research", "")
                    if rules:
                        print(f"[Research] 🎓 Using latest rules: {rules[:50]}...", flush=True)
            except: pass

        # ۲. استخراج هوشمند کلمات کلیدی (هر چیزی بعد از کلمه for)
        text = task.description
        if " for " in text.lower():
            query = text.lower().split(" for ", 1)[1]
        else:
            query = text
        
        clean_query = query.strip()
        encoded_query = urllib.parse.quote(clean_query)
        
        print(f"[Research] 🔍 Searching GitHub for: {clean_query}", flush=True)
        url = f"https://api.github.com/search/repositories?q={encoded_query}&sort=stars&order=desc&per_page=1"
        
        save_dir = "/sdcard/omid-ai/sandbox_downloads"
        os.makedirs(save_dir, exist_ok=True)
        
        try:
            async with httpx.AsyncClient() as client:
                headers = {"User-Agent": "OMID-AI"}
                resp = await client.get(url, headers=headers, timeout=15.0)
                
                if resp.status_code == 200:
                    data = resp.json()
                    items = data.get("items", [])
                    if not items:
                        self.log_event("chat", {"text": f"❌ پروژه‌ای برای '{clean_query}' پیدا نشد."})
                        return Result(task_id=task.id, success=False, output="Not found")
                    
                    item = items[0]
                    repo_name = item['name']
                    owner = item['owner']['login']
                    
                    contents_url = f"https://api.github.com/repos/{owner}/{repo_name}/contents"
                    contents_resp = await client.get(contents_url, headers=headers, timeout=15.0)
                    
                    if contents_resp.status_code == 200:
                        files = contents_resp.json()
                        target_file_url = None
                        target_file_name = None
                        
                        for f in files:
                            if f['type'] == 'file' and (f['name'].endswith('.py') or f['name'].lower() == 'readme.md'):
                                target_file_url = f['download_url']
                                target_file_name = f['name']
                                break
                        
                        if target_file_url:
                            code_resp = await client.get(target_file_url, timeout=15.0)
                            if code_resp.status_code == 200:
                                code_content = code_resp.text
                                file_path = os.path.join(save_dir, f"{repo_name}_{target_file_name}")
                                with open(file_path, "w", encoding="utf-8") as f:
                                    f.write(code_content)
                                    
                                msg = f"✅ پروژه **{repo_name}** دانلود شد (فایل: `{target_file_name}`) و در `{file_path}` ذخیره شد."
                                self.log_event("chat", {"text": msg})
                                return Result(task_id=task.id, success=True, output=code_content)
                        
                        self.log_event("chat", {"text": f"❌ فایل پایتون یا README در پروژه {repo_name} پیدا نشد."})
                        return Result(task_id=task.id, success=False, output="No valid file found")
                    else:
                        self.log_event("chat", {"text": "❌ خطا در دریافت لیست فایل‌های گیت‌هاب."})
                        return Result(task_id=task.id, success=False, output="API Error")
                else:
                    self.log_event("chat", {"text": "❌ خطای گیت‌هاب (احتمالاً محدودیت درخواست)."})
                    return Result(task_id=task.id, success=False, output="GitHub API Error")
        except Exception as e:
            self.log_event("chat", {"text": f"❌ خطا: {str(e)}"})
            return Result(task_id=task.id, success=False, output=str(e))
