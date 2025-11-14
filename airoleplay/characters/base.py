"""Base character class for defining roleplay characters."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class Character:
    """Represents a roleplay character with personality and background."""

    name: str
    personality: str
    background: str
    age: Optional[int] = None
    occupation: Optional[str] = None
    traits: Optional[list[str]] = None
    speaking_style: Optional[str] = None

    def get_system_prompt(self) -> str:
        """Generate a system prompt for this character."""
        prompt_parts = [
            f"You are {self.name}.",
            f"\nPersonality: {self.personality}",
            f"\nBackground: {self.background}",
        ]

        if self.age:
            prompt_parts.append(f"\nAge: {self.age}")

        if self.occupation:
            prompt_parts.append(f"\nOccupation: {self.occupation}")

        if self.traits:
            traits_str = ", ".join(self.traits)
            prompt_parts.append(f"\nKey traits: {traits_str}")

        if self.speaking_style:
            prompt_parts.append(f"\nSpeaking style: {self.speaking_style}")

        prompt_parts.append(
            "\n\nStay in character throughout the conversation. "
            "Respond naturally as this character would, considering their "
            "personality, background, and current situation."
        )

        return "".join(prompt_parts)

    def __str__(self) -> str:
        return f"Character: {self.name} ({self.occupation or 'Unknown occupation'})"
