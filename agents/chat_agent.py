"""OMID AI - Chat Agent with SQLite Memory"""
import os
import json
import httpx
import re
from agents.base import BaseAgent, Task, Result
from core.db import get_db

class ChatAgent(BaseAgent):
    name = "ChatAgent"
    display_name = "Assistant"

    async def execute(self, task: Task) -> Result:
        user_msg = task.description
        db = get_db()

        # Load memory from SQLite (returns a dict)
        memory = db.get_preferences()
        if not isinstance(memory, dict):
            memory = {}
        print(f"[ChatAgent] Loaded memory: {memory}")

        # Load history from SQLite
        history = db.get_recent_messages(10)

        prompt = f"""You are OMID AI, a highly intelligent and helpful AI assistant.
Respond to the user in Persian.
User context (Memory): {json.dumps(memory, ensure_ascii=False)}
History: {json.dumps(history, ensure_ascii=False)}
User says: {user_msg}

CRITICAL INSTRUCTION: If the user is giving you a personal fact (like their name, job, or interests), you MUST extract it and output a JSON block at the VERY END of your response exactly like this:
<SAVE_MEMORY>{{"name": "Ali", "job": "Engineer"}}</SAVE_MEMORY>
If there is no new personal fact, DO NOT include the SAVE_MEMORY block.
"""

        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    "http://127.0.0.1:5001/v1/chat/completions",
                    json={
                        "model": "openai/gpt-oss-120b",
                        "messages": [{"role": "user", "content": prompt}]
                    },
                    timeout=60.0
                )
                data = resp.json()

                if "choices" not in data:
                    return Result(task_id=task.id, success=False, output="Error communicating with Router.")

                reply = data["choices"][0]["message"]["content"]

            # Extract and save memory BEFORE stripping the tag
            match = re.search(r"<SAVE_MEMORY>(.*?)</SAVE_MEMORY>", reply, re.DOTALL)
            if match:
                try:
                    new_facts = json.loads(match.group(1))
                    memory.update(new_facts)
                    db.set_preferences(memory)
                    print(f"[ChatAgent] Memory saved: {new_facts}")
                    print(f"[ChatAgent] Full memory now: {memory}")
                except Exception as e:
                    print(f"[ChatAgent] Memory save error: {e}")

            # ALWAYS strip the SAVE_MEMORY tag before displaying, 
            # even if the save above failed.
            reply = re.sub(r"<SAVE_MEMORY>.*?</SAVE_MEMORY>", "", reply, flags=re.DOTALL).strip()

            # Save to history
            db.add_message("user", user_msg)
            db.add_message("assistant", reply)

            self.log_event("chat", {"text": reply})
            return Result(task_id=task.id, success=True, output=reply)

        except Exception as e:
            print(f"[ChatAgent] Error: {e}")
            return Result(task_id=task.id, success=False, output=str(e))
