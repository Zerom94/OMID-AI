import os
import asyncio
import httpx
import json
import re
import shutil
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
        self.log_event("working", {"agent": self.name, "status": "Thinking..."})
        
        # اگر درخواست ساخت اپلیکیشن بود، فقط برنامه‌نویس را صدا بزن
        if goal.strip().startswith("!develop") or any(k in goal.lower() for k in ["سایت", "وب", "app", "site", "اپلیکیشن"]):
            self.log_event("working", {"agent": self.name, "status": "Planning Python App..."})
            tasks = [
                Task(id="t1", description=goal.replace("!develop", "").strip(), agent_id="developer", priority=3)
            ]
        else:
            # درخواست چت عادی
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

        return results

    def _get_agent(self, agent_id: str):
        if agent_id == "developer":
            from agents.developer import DeveloperAgent
            return DeveloperAgent(self.config)
        elif agent_id == "chat":
            from agents.chat_agent import ChatAgent
            return ChatAgent(self.config)
        elif agent_id == "security":
            from agents.security_agent import SecurityAgent
            return SecurityAgent(self.config)
        elif agent_id == "quality_control":
            from agents.quality_control import QualityControlAgent
            return QualityControlAgent(self.config, memory=self.memory)
        elif agent_id == "research":
            from agents.research_agent import ResearchAgent
            return ResearchAgent(self.config)
        elif agent_id == "recon":
            from agents.recon_agent import ReconAgent
            return ReconAgent(self.config)
        return None
