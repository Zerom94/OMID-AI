import os
import asyncio
import httpx
import json
import re
import shutil
import traceback
from agents.base import BaseAgent, Task, Result

class ManagerAgent(BaseAgent):
    name = "Manager"
    display_name = "Manager"

    def __init__(self, config=None, memory=None):
        super().__init__(config, memory)
        self.router_url = "http://127.0.0.1:5001/v1/chat/completions"

    async def execute(self, task: Task) -> Result:
        return Result(task_id=task.id, success=True)

    async def plan_and_dispatch(self, goal: str) -> list:
        if goal.strip().startswith("!evolve"):
            parts = goal.split()
            if len(parts) > 1:
                target_file = parts[1]
                file_path = os.path.join("agents", target_file)
                backup_path = file_path + ".bak"
                self.log_event("working", {"agent": self.name, "status": f"Evolving {target_file}..."})
                if os.path.exists(file_path):
                    shutil.copy(file_path, backup_path)
                    with open(file_path, "r") as f: current_code = f.read()
                    prompt = f"Rewrite this code to be better. Output ONLY raw python code:\n\n{current_code}"
                    try:
                        async with httpx.AsyncClient() as client:
                            resp = await client.post(self.router_url, json={"model": "openai/gpt-oss-120b", "messages": [{"role": "user", "content": prompt}]}, timeout=120.0)
                            new_code = resp.json()["choices"][0]["message"]["content"].strip()
                            if new_code.startswith("```python"): new_code = new_code[9:]
                            if new_code.endswith("```"): new_code = new_code[:-3]
                            with open(file_path, "w") as f: f.write(new_code.strip())
                            self.log_event("chat", {"text": f"✅ فایل {target_file} با موفقیت ارتقا یافت."})
                    except Exception as e:
                        shutil.copy(backup_path, file_path)
                        self.log_event("chat", {"text": f"❌ خطا در ارتقا: {e}"})
                self.log_event("complete", {"agent": self.name, "status": "Done"})
                return []

        if goal.strip().lower().startswith("security scan") or "scan http" in goal.lower():
            self.log_event("working", {"agent": self.name, "status": "Security Scan..."})
            agent = self._get_agent("security")
            res = await agent.execute(Task(id="sec_task", description=goal, agent_id="security", priority=3))
            self.log_event("working", {"agent": "QC", "status": "Working"})
            await self._get_agent("quality_control").execute(Task(id="qc", description="Final QC", agent_id="quality_control", priority=2))
            self.log_event("complete", {"agent": "QC", "status": "Done"})
            self.log_event("complete", {"agent": self.name, "status": "Done"})
            return [res]

        self.log_event("working", {"agent": self.name, "status": "Thinking..."})
        prompt = f"""You are OMID AI. User says: {goal}
If chat, output {{"type": "chat"}}. If mission, output {{"type": "mission", "tasks": [{{"agent": "developer", "description": "..."}}]}}. Output ONLY valid JSON."""
        
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(self.router_url, json={"model": "openai/gpt-oss-120b", "messages": [{"role": "user", "content": prompt}], "response_format": {"type": "json_object"}}, timeout=60.0)
                raw_plan = resp.json()["choices"][0]["message"]["content"]
                match = re.search(r'(\{.*\})', raw_plan, re.DOTALL)
                plan_data = json.loads(match.group(0)) if match else {"type": "chat"}
        except Exception:
            plan_data = {"type": "chat"}

        if plan_data.get("type") == "chat":
            tasks = [Task(id="chat", description=goal, agent_id="chat", priority=3)]
        else:
            tasks = [Task(id=f"t{i}", description=t.get("description", ""), agent_id=t.get("agent", "developer"), priority=3) for i, t in enumerate(plan_data.get("tasks", []))]
            if not tasks:
                tasks = [Task(id="chat", description=goal, agent_id="chat", priority=3)]

        results = []
        for t in tasks:
            self.log_event("working", {"agent": t.agent_id.capitalize(), "status": "Working"})
            try:
                agent = self._get_agent(t.agent_id)
                if agent:
                    res = await agent.execute(t)
                    if res and res.success:
                        self.log_event("complete", {"agent": t.agent_id.capitalize(), "status": "Done"})
                    else:
                        err_msg = res.output if res else "Unknown"
                        self.log_event("fail", {"agent": t.agent_id.capitalize(), "status": f"Failed: {err_msg}"})
                    results.append(res)
                else:
                    self.log_event("fail", {"agent": t.agent_id.capitalize(), "status": "Failed: Agent not found"})
            except Exception as e:
                self.log_event("fail", {"agent": t.agent_id.capitalize(), "status": f"Failed: {str(e)}"})
            await asyncio.sleep(0.5)

        is_simple_chat = (len(tasks) == 1 and tasks[0].agent_id == "chat")
        if not is_simple_chat:
            self.log_event("working", {"agent": "QC", "status": "Working"})
            await self._get_agent("quality_control").execute(Task(id="qc", description="Final QC", agent_id="quality_control", priority=2))
            self.log_event("complete", {"agent": "QC", "status": "Done"})

        return results

    def _get_agent(self, agent_id: str):
        if agent_id == "developer":
            from agents.developer import DeveloperAgent
            return DeveloperAgent(self.config)
        elif agent_id == "quality_control":
            from agents.quality_control import QualityControlAgent
            return QualityControlAgent(self.config, memory=self.memory)
        elif agent_id == "chat":
            from agents.chat_agent import ChatAgent
            return ChatAgent(self.config)
        elif agent_id == "security":
            from agents.security_agent import SecurityAgent
            return SecurityAgent(self.config)
        elif agent_id == "recon":
            from agents.recon_agent import ReconAgent
            return ReconAgent(self.config)
        elif agent_id == "auditor":
            from agents.auditor import AuditorAgent
            return AuditorAgent(self.config)
        elif agent_id == "research":
            from agents.research_agent import ResearchAgent
            return ResearchAgent(self.config)
