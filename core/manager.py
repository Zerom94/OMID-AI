"""OMID AI - Manager Agent with Direct Command Bypass"""
import os
import asyncio
import httpx
import json
import re
from agents.base import BaseAgent, Task, Result
from core.db import get_db

class ManagerAgent(BaseAgent):
    name = "Manager"
    display_name = "Manager"

    def __init__(self, config=None, memory=None):
        super().__init__(config, memory)
        self.router_url = "http://127.0.0.1:5001/v1/chat/completions"
        self.available_agents = {
            "chat": "General conversation, greetings, and answering questions.",
            "developer": "Writing code, building Python applications.",
            "security": "Ethical hacking, security scans, Nmap.",
            "research": "Searching the web, finding information.",
            "auditor": "Reviewing code security, finding vulnerabilities.",
            "content": "Writing articles, SEO content, social media posts.",
            "recon": "Reconnaissance and information gathering."
        }

    async def execute(self, task: Task) -> Result:
        return Result(task_id=task.id, success=True)

    async def plan_and_dispatch(self, goal: str) -> list:
        self.log_event("working", {"agent": self.name, "status": "Analyzing request..."})

        # DIRECT COMMAND BYPASS - NO LLM Routing needed
        if goal.startswith("!evolve"):
            return await self._handle_evolve_command(goal)
        if goal.startswith("!develop"):
            return await self._handle_develop_command(goal)
        if goal.startswith("!security"):
            return await self._handle_security_command(goal)

        # For other commands, use LLM routing
        return await self._route_with_llm(goal)

    async def _handle_evolve_command(self, goal: str) -> list:
        parts = goal.split()
        if len(parts) > 1:
            target_file = parts[1]
            file_path = os.path.join("/sdcard/omid-ai", target_file)
            if os.path.exists(file_path):
                self.log_event("working", {"agent": "Evolve", "status": f"Upgrading {target_file}..."})
                with open(file_path, "r", encoding="utf-8") as f:
                    current_code = f.read()
                prompt = f"You are an expert Python developer. Optimize and improve the following code. Output ONLY the raw python code without explanations or markdown wrappers.\n\n{current_code}"
                try:
                    async with httpx.AsyncClient() as client:
                        resp = await client.post(self.router_url, json={"model": "openai/gpt-oss-120b", "messages": [{"role": "user", "content": prompt}]}, timeout=120.0)
                        data = resp.json()
                        new_code = data["choices"][0]["message"]["content"]
                        new_code = new_code.replace("```python", "").replace("```", "").strip()
                        os.rename(file_path, file_path + ".bak")
                        with open(file_path, "w", encoding="utf-8") as f:
                            f.write(new_code)
                        self.log_event("chat", {"text": f"✅ فایل {target_file} با موفقیت ارتقا یافت (نسخه پشتیبان در {target_file}.bak ذخیره شد)."})
                        self.log_event("complete", {"agent": "Evolve", "status": "Done"})
                        return []
                except Exception as e:
                    self.log_event("fail", {"agent": "Evolve", "status": str(e)})
                    return []
            else:
                self.log_event("chat", {"text": f"❌ فایل {target_file} پیدا نشد."})
                return []
        return []

    async def _handle_develop_command(self, goal: str) -> list:
        self.log_event("working", {"agent": "Developer", "status": "Routing to Developer..."})
        task = Task(id="t1", description=goal.replace("!develop", "").strip(), agent_id="developer", priority=3)
        agent = self._get_agent("developer")
        res = await agent.execute(task)
        return [res]

    async def _handle_security_command(self, goal: str) -> list:
        self.log_event("working", {"agent": "Security", "status": "Routing to Security Agent..."})
        task = Task(id="t_sec", description=goal.replace("!security scan", "").replace("!security", "").strip(), agent_id="security", priority=3)
        agent = self._get_agent("security")
        res = await agent.execute(task)
        return [res]

    async def _route_with_llm(self, goal: str) -> list:
        agents_list_str = "\n".join([f"- {k}: {v}" for k, v in self.available_agents.items()])
        routing_prompt = f"""You are the Manager of OMID AI. Route the user request to the correct agent.
Available Agents:
{agents_list_str}

User Request: "{goal}"

Output ONLY a valid JSON object:
{{"agent_id": "choose from list", "description": "cleaned up request", "priority": 3}}
Do NOT output any conversational text or explanations. Just the JSON.
"""
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(self.router_url, json={"model": "openai/gpt-oss-120b", "messages": [{"role": "user", "content": routing_prompt}], "response_format": {"type": "json_object"}}, timeout=30.0)
                raw_route = resp.json()["choices"][0]["message"]["content"]
                match = re.search(r'\{.*\}', raw_route, re.DOTALL)
                if match:
                    route_data = json.loads(match.group(0))
                else:
                    route_data = {"agent_id": "chat", "description": goal}
        except Exception as e:
            self.log_event("chat", {"text": f"⚠️ خطا در مسیریابی هوشمند، ارجاع پیش‌فرض به بخش چت: {str(e)}"})
            route_data = {"agent_id": "chat", "description": goal}

        target_agent = route_data.get("agent_id", "chat")
        task_desc = route_data.get("description", goal)

        if target_agent not in self.available_agents:
            target_agent = "chat"

        self.log_event("working", {"agent": self.name, "status": f"Routing to {target_agent.capitalize()}..."})
        task = Task(id="t_main", description=task_desc, agent_id=target_agent, priority=route_data.get("priority", 3))
        
        results = []
        self.log_event("working", {"agent": target_agent.capitalize(), "status": "Working"})
        try:
            agent = self._get_agent(target_agent)
            if agent:
                res = await agent.execute(task)
                if res and res.success:
                    self.log_event("complete", {"agent": target_agent.capitalize(), "status": "Done"})
                else:
                    err_msg = res.output if res else "Unknown"
                    self.log_event("fail", {"agent": target_agent.capitalize(), "status": f"Failed: {err_msg}"})
                results.append(res)
            else:
                self.log_event("fail", {"agent": target_agent.capitalize(), "status": "Failed: Agent not found"})
        except Exception as e:
            self.log_event("fail", {"agent": target_agent.capitalize(), "status": f"Failed: {str(e)}"})
        return results

    def _get_agent(self, agent_id: str):
        agents_map = {
            "content": ("agents.content_agent", "ContentAgent"),
            "developer": ("agents.developer", "DeveloperAgent"),
            "chat": ("agents.chat_agent", "ChatAgent"),
            "security": ("agents.security_agent", "SecurityAgent"),
            "research": ("agents.research_agent", "ResearchAgent"),
            "recon": ("agents.recon_agent", "ReconAgent")
        }
        if agent_id in agents_map:
            module_name, class_name = agents_map[agent_id]
            try:
                module = __import__(module_name, fromlist=[class_name])
                agent_class = getattr(module, class_name)
                return agent_class(config=self.config, memory=self.memory)
            except Exception as e:
                print(f"Error loading agent {agent_id}: {e}")
                return None
        return None
