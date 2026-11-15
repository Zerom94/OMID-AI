from core.memory_rag import generate_response

class ChatAgent:
    """Chat agent that delegates response generation to the RAG system.
    The RAG's `generate_response` automatically builds the system prompt using
    the user's stored memory (name, occupation, interests).
    """

    def get_response(self, user_input: str) -> str:
        """Return the agent's reply for *user_input*.
        The memory integration is handled inside `generate_response`.
        """
        return generate_response(user_input)
