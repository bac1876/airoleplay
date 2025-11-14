"""Roleplay agent implementation using LangChain."""

import os
from typing import Optional, List

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

from ..characters.base import Character


class RoleplayAgent:
    """An agent that roleplays as a specific character using LangChain."""

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
        self.system_prompt = character.get_system_prompt()
        self.message_history: List = []

        # Initialize the LLM
        self.llm = ChatAnthropic(
            model=self.model_name,
            temperature=self.temperature,
            api_key=api_key or os.getenv("ANTHROPIC_API_KEY"),
        )

    def chat(self, message: str, thread_id: Optional[str] = None) -> str:
        """Send a message to the character and get a response.

        Args:
            message: The message to send
            thread_id: Optional thread ID for conversation continuity (not used in this implementation)

        Returns:
            The character's response
        """
        # Build messages with system prompt and history
        messages = [SystemMessage(content=self.system_prompt)]
        messages.extend(self.message_history)
        messages.append(HumanMessage(content=message))

        # Invoke the LLM
        response = self.llm.invoke(messages)

        # Store in history
        self.message_history.append(HumanMessage(content=message))
        self.message_history.append(AIMessage(content=response.content))

        return response.content

    async def achat(self, message: str, thread_id: Optional[str] = None) -> str:
        """Async version of chat.

        Args:
            message: The message to send
            thread_id: Optional thread ID for conversation continuity (not used in this implementation)

        Returns:
            The character's response
        """
        # Build messages with system prompt and history
        messages = [SystemMessage(content=self.system_prompt)]
        messages.extend(self.message_history)
        messages.append(HumanMessage(content=message))

        # Invoke the LLM asynchronously
        response = await self.llm.ainvoke(messages)

        # Store in history
        self.message_history.append(HumanMessage(content=message))
        self.message_history.append(AIMessage(content=response.content))

        return response.content

    def get_character_info(self) -> str:
        """Get information about the current character."""
        return str(self.character)
