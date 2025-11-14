"""Enhanced character class for CFR-based roleplay personas."""

import json
import random
from pathlib import Path
from typing import Optional, Dict, List, Any
from dataclasses import dataclass, field


@dataclass
class ObjectionPattern:
    """Represents an objection the persona can raise."""
    name: str
    trigger_phrases: List[str]
    emotion: str
    response_playbook: List[str]
    evidence: List[str]
    magic_phrases: List[str]


@dataclass
class PersonaCharacter:
    """A roleplay persona with CFR technique integration."""

    id: str
    label: str
    tone: Dict[str, Any]
    persona_traits: List[str]
    context: Dict[str, Any]
    goals: List[str]
    objection_patterns: List[ObjectionPattern]
    knowledge_snippets: List[str]
    escalation_rules: Dict[str, Any]

    # Internal state
    current_objection_index: int = 0
    cooperation_level: int = 5  # 0-10, higher = more cooperative
    objections_raised: List[str] = field(default_factory=list)
    agent_technique_quality: int = 0  # Tracks how well agent is doing

    @classmethod
    def from_json(cls, json_path: str) -> "PersonaCharacter":
        """Load a persona from JSON file."""
        with open(json_path, 'r') as f:
            data = json.load(f)

        # Convert objection_patterns to ObjectionPattern objects
        objections = [
            ObjectionPattern(
                name=obj['name'],
                trigger_phrases=obj['trigger_phrases'],
                emotion=obj['emotion'],
                response_playbook=obj['response_playbook'],
                evidence=obj['evidence'],
                magic_phrases=obj['magic_phrases']
            )
            for obj in data['objection_patterns']
        ]

        return cls(
            id=data['id'],
            label=data['label'],
            tone=data['tone'],
            persona_traits=data['persona_traits'],
            context=data['context'],
            goals=data['goals'],
            objection_patterns=objections,
            knowledge_snippets=data['knowledge_snippets'],
            escalation_rules=data['escalation_rules']
        )

    def get_system_prompt(self, difficulty: str = "medium") -> str:
        """Generate system prompt for this persona with CFR integration."""
        prompt_parts = []

        # Base persona description
        prompt_parts.append(f"You are a roleplay client persona: {self.label}")
        prompt_parts.append(f"\nPersona ID: {self.id}")
        prompt_parts.append(f"\nTraits: {', '.join(self.persona_traits)}")

        # Tone instructions
        prompt_parts.append(f"\n\n## Speaking Style:")
        prompt_parts.append(f"- Formality: {self.tone['formality']}")
        prompt_parts.append(f"- Energy level: {self.tone['energy']}")
        prompt_parts.append(f"- Pace: ~{self.tone['pace_wpm']} words per minute")
        prompt_parts.append(f"- Directness: {self.tone['directness']}")
        prompt_parts.append("\n- Keep responses under 90 words unless explicitly asked for detail")

        # Context
        prompt_parts.append(f"\n\n## Your Situation:")
        for key, value in self.context.items():
            prompt_parts.append(f"- {key.replace('_', ' ').title()}: {value}")

        # Goals
        prompt_parts.append(f"\n\n## Your Goals:")
        for goal in self.goals:
            prompt_parts.append(f"- {goal}")

        # Objection handling instructions
        prompt_parts.append(f"\n\n## Objection Behavior:")
        prompt_parts.append(f"- Current cooperation level: {self.cooperation_level}/10")

        if self.cooperation_level < 4:
            prompt_parts.append("- You are resistant and skeptical. Push back on suggestions.")
        elif self.cooperation_level < 7:
            prompt_parts.append("- You are cautiously interested. Need convincing.")
        else:
            prompt_parts.append("- You are cooperative and ready to move forward.")

        # Add available objections based on difficulty
        if difficulty == "beginner":
            objections_to_use = self.objection_patterns[:2]  # Easy objections only
        elif difficulty == "advanced":
            objections_to_use = self.objection_patterns  # All objections
        else:  # medium
            objections_to_use = self.objection_patterns[:4]

        prompt_parts.append(f"\n\n## Objections You May Raise:")
        prompt_parts.append("Trigger ONE objection per conversation turn maximum.")
        prompt_parts.append("Only raise objection if conversation naturally leads to it.")
        prompt_parts.append("\nAvailable objections:")
        for obj in objections_to_use:
            prompt_parts.append(f"- {obj.name}: {', '.join(obj.trigger_phrases[:2])}")

        # CFR technique response instructions
        prompt_parts.append(f"\n\n## How to Respond Based on Agent's Technique:")
        prompt_parts.append("\nIf agent uses proper CFR techniques (Acknowledge/Affirm, Isolate, etc.):")
        prompt_parts.append("- Become MORE cooperative")
        prompt_parts.append("- Answer questions directly")
        prompt_parts.append("- Move conversation forward")

        prompt_parts.append("\nIf agent argues, rushes, or breaks rapport:")
        prompt_parts.append("- Become LESS cooperative")
        prompt_parts.append("- Add new objections")
        prompt_parts.append("- Be more resistant")

        # Rapport breakers to watch for
        prompt_parts.append("\n\nRapport breakers that make you less cooperative:")
        prompt_parts.append("- Agent says 'I understand' without qualifier")
        prompt_parts.append("- Agent argues with you")
        prompt_parts.append("- Agent speaks too fast or doesn't listen")
        prompt_parts.append("- Agent skips isolation (doesn't ask if there are other concerns)")

        # Knowledge snippets
        if self.knowledge_snippets:
            prompt_parts.append(f"\n\n## Knowledge you have:")
            for snippet in self.knowledge_snippets[:3]:  # Limit to 3
                prompt_parts.append(f"- {snippet}")

        # Escalation
        if self.escalation_rules.get('handoff_if'):
            prompt_parts.append(f"\n\n## Escalation:")
            prompt_parts.append(f"If agent asks about: {', '.join(self.escalation_rules['handoff_if'][:2])}")
            prompt_parts.append(f'Say: "That\'s a great question - let me connect you with {self.escalation_rules[\"handoff_target\"]}"')

        # Final instructions
        prompt_parts.append("\n\n## Important:")
        prompt_parts.append("- Stay in character throughout")
        prompt_parts.append("- One objection per turn maximum")
        prompt_parts.append("- Respond naturally based on your personality")
        prompt_parts.append("- Let the agent practice their techniques")
        prompt_parts.append("- Be realistic - don't make it too easy or too hard")

        return "".join(prompt_parts)

    def adjust_cooperation(self, agent_response_quality: int):
        """Adjust cooperation level based on agent's technique quality.

        Args:
            agent_response_quality: Score from 0-10 on how well agent responded
        """
        if agent_response_quality >= 8:
            self.cooperation_level = min(10, self.cooperation_level + 2)
        elif agent_response_quality >= 5:
            self.cooperation_level = min(10, self.cooperation_level + 1)
        elif agent_response_quality < 3:
            self.cooperation_level = max(0, self.cooperation_level - 2)
        else:
            self.cooperation_level = max(0, self.cooperation_level - 1)

    def get_next_objection(self) -> Optional[ObjectionPattern]:
        """Get the next objection to potentially raise."""
        if self.current_objection_index >= len(self.objection_patterns):
            return None

        objection = self.objection_patterns[self.current_objection_index]
        self.current_objection_index += 1
        self.objections_raised.append(objection.name)
        return objection

    def reset_conversation(self):
        """Reset persona state for new conversation."""
        self.current_objection_index = 0
        self.cooperation_level = 5
        self.objections_raised = []
        self.agent_technique_quality = 0

    def get_suggested_magic_phrase(self, objection_name: str) -> List[str]:
        """Get magic phrases suggested for handling a specific objection."""
        for obj in self.objection_patterns:
            if obj.name == objection_name:
                return obj.magic_phrases
        return []

    def __str__(self) -> str:
        return f"Persona: {self.label} (Cooperation: {self.cooperation_level}/10)"
