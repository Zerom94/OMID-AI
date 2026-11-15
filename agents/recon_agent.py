import os
from agents.base import BaseAgent, Task, Result

class ReconAgent(BaseAgent):
    name = "Recon"
    display_name = "Recon"

    async def execute(self, task: Task) -> Result:
        self.log_event("working", {"agent": self.name, "status": "Reconnaissance..."})
        result_text = f"Recon completed for: {task.description}"
        self.log_event("complete", {"agent": self.name, "status": "Done"})
        return Result(task_id=task.id, success=True, output=result_text)
