import os
import json
import httpx
import re
from agents.base import BaseAgent, Task, Result

class ChatAgent(BaseAgent):
    name = "ChatAgent"
    display_name = "Assistant"

    async def execute(self, task: Task) -> Result:
        user_msg = task.description
        history_file = "/sdcard/omid-ai/chat_history.json"
        memory_file = "/sdcard/omid-ai/memory_rag.json"

        # 1. Load Memory
        memory = {}
        if os.path.exists(memory_file):
            try:
                with open(memory_file, "r", encoding="utf-8") as f:
                    memory = json.load(f)
            except Exception:
                pass

        # 2. Load History
        history = []
        if os.path.exists(history_file):
            try:
                with open(history_file, "r", encoding="utf-8") as f:
                    history = json.load(f)
            except Exception:
                pass

        # 3. Build Prompt
        prompt = f"""You are OMID AI, a highly intelligent and helpful AI assistant.
Respond to the user in Persian.
User context (Memory): {json.dumps(memory, ensure_ascii=False)}
History: {json.dumps(history[-4:], ensure_ascii=False)}
User says: {user_msg}

CRITICAL INSTRUCTION: If the user is giving you a personal fact (like their name, job, or interests), you MUST extract it and output a JSON block at the VERY END of your response exactly like this:
<SAVE_MEMORY>{{"name": "Ali", "job": "Engineer"}}</SAVE_MEMORY>
If there is no new personal fact, DO NOT include the SAVE_MEMORY block.
"""

        try:
            # 4. Call AI
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    "http://127.0.0.1:5001/v1/chat/completions",
                    json={"model": "openai/gpt-oss-120b", "messages": [{"role": "user", "content": prompt}]},
                    timeout=60.0
                )
                data = resp.json()
                
                if "choices" not in data:
                    return Result(task_id=task.id, success=False, output="Error communicating with Router.")

                reply = data["choices"][0]["message"]["content"]

            # 5. Extract Memory
            match = re.search(r"<SAVE_MEMORY>(.*?)</SAVE_MEMORY>", reply, re.DOTALL)
            if match:
                try:
                    new_facts = json.loads(match.group(1))
                    memory.update(new_facts)
                    with open(memory_file, "w", encoding="utf-8") as f:
                        json.dump(memory, f, ensure_ascii=False, indent=2)
                    # Remove the tag from the reply shown to user
                    reply = re.sub(r"<SAVE_MEMORY>.*?</SAVE_MEMORY>", "", reply, flags=re.DOTALL).strip()
                    print(f"[ChatAgent] 💾 Memory saved: {new_facts}")
                except Exception:
                    pass

            # 6. Save History
            history.append({"role": "user", "content": user_msg})
            history.append({"role": "assistant", "content": reply})
            with open(history_file, "w", encoding="utf-8") as f:
                json.dump(history[-10:], f, ensure_ascii=False, indent=2)

            # 🔴 این خط مهم‌ترین بخش است: ارسال جواب به داشبورد
            self.log_event("chat", {"text": reply})

            return Result(task_id=task.id, success=True, output=reply)

        except Exception as e:
            return Result(task_id=task.id, success=False, output=str(e))
