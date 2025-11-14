"""Roleplay agent implementation using deepagents."""

import os
from typing import Optional

from langchain_anthropic import ChatAnthropic
from deepagents import create_agent
from deepagents.core import AgentState
from langgraph.graph import StateGraph

from ..characters.base import Character


class RoleplayAgent:
    """An agent that roleplays as a specific character using deepagents."""

    def __init__(
        self,
        character: Character,
        model_name: Optional[str] = None,
        temperature: float = 0.7,
        api_key: Optional[str] = None,
    ):
        """Initialize the roleplay agent.

        Args:
            character: The character to roleplay as
            model_name: Model to use (defaults to claude-sonnet-4-5)
            temperature: Temperature for generation (0.0-1.0)
            api_key: Anthropic API key (or uses ANTHROPIC_API_KEY env var)
        """
        self.character = character
        self.model_name = model_name or os.getenv(
            "DEFAULT_MODEL", "claude-sonnet-4-5-20250929"
        )
        self.temperature = temperature

        # Initialize the LLM
        self.llm = ChatAnthropic(
            model=self.model_name,
            temperature=self.temperature,
            api_key=api_key or os.getenv("ANTHROPIC_API_KEY"),
        )

        # Create the agent with character's system prompt
        self.agent = create_agent(
            model=self.llm,
            system_prompt=character.get_system_prompt(),
        )

    def chat(self, message: str, thread_id: Optional[str] = None) -> str:
        """Send a message to the character and get a response.

        Args:
            message: The message to send
            thread_id: Optional thread ID for conversation continuity

        Returns:
            The character's response
        """
        config = {"configurable": {}}
        if thread_id:
            config["configurable"]["thread_id"] = thread_id

        # Invoke the agent
        result = self.agent.invoke(
            {"messages": [("user", message)]},
            config=config
        )

        # Extract the response
        if result and "messages" in result:
            # Get the last AI message
            for msg in reversed(result["messages"]):
                if hasattr(msg, "type") and msg.type == "ai":
                    return msg.content
                elif isinstance(msg, tuple) and msg[0] == "ai":
                    return msg[1]

        return "I'm not sure how to respond to that."

    async def achat(self, message: str, thread_id: Optional[str] = None) -> str:
        """Async version of chat.

        Args:
            message: The message to send
            thread_id: Optional thread ID for conversation continuity

        Returns:
            The character's response
        """
        config = {"configurable": {}}
        if thread_id:
            config["configurable"]["thread_id"] = thread_id

        # Invoke the agent asynchronously
        result = await self.agent.ainvoke(
            {"messages": [("user", message)]},
            config=config
        )

        # Extract the response
        if result and "messages" in result:
            for msg in reversed(result["messages"]):
                if hasattr(msg, "type") and msg.type == "ai":
                    return msg.content
                elif isinstance(msg, tuple) and msg[0] == "ai":
                    return msg[1]

        return "I'm not sure how to respond to that."

    def get_character_info(self) -> str:
        """Get information about the current character."""
        return str(self.character)
