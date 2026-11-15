import logging
from core.memory_rag import generate_response

class ChatAgent:
    """Simple chat agent that forwards user input to the RAG generator.

    The ``generate_response`` function builds the system prompt using the user's
    memory (name, occupation, interests) and returns the AI's reply.
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def get_response(self, user_message: str) -> str:
        """Return the AI response for *user_message*.

        Args:
            user_message: The raw input from the user.
        Returns:
            The generated response string.
        """
        self.logger.debug("Forwarding message to generate_response: %s", user_message)
        return generate_response(user_message)
