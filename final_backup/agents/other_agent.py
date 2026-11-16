from agents.base import BaseAgent, Task, Result
import logging
import time

logger = logging.getLogger("OtherAgent")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter("[%(name)s] %(asctime)s - %(levelname)s: %(message)s"))
logger.addHandler(handler)

class OtherAgent(BaseAgent):
    name = "Other"
    display_name = "Other"

    async def execute(self, task: Task) -> Result:
        """
        Handle a task in a more robust manner:
        - Log fast and informative messages using the logger.
        - Capture and report any exception, returning a Result with success=False.
        - Return execution time in the output for monitoring.
        """
        start = time.perf_counter()
        try:
            if not task or not hasattr(task, "description"):
                raise ValueError("Invalid task object: missing required attributes.")

            logger.info(f"Handling task: {task.description}")

            # Placeholder for real business logic. Replace with actual implementation.
            output = f"Task handled by Other Agent: {task.description}"
            success = True
        except Exception as exc:
            logger.exception("Error while handling task")
            output = f"Error: {type(exc).__name__}: {exc}"
            success = False
        finally:
            elapsed = time.perf_counter() - start
            output += f" | Execution time: {elapsed:.4f}s"

        return Result(task_id=task.id, success=success, output=output)