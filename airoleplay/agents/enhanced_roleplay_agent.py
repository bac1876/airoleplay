"""Enhanced roleplay agent with CFR scoring and training modes."""

import os
from typing import Optional, List, Tuple
from pathlib import Path

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

from ..characters.persona_character import PersonaCharacter
from ..scoring.conversation_scorer import ConversationScorer, TurnScore


class EnhancedRoleplayAgent:
    """Roleplay agent with CFR integration and real-time scoring."""

    def __init__(
        self,
        persona: PersonaCharacter,
        difficulty: str = "medium",
        training_mode: str = "scoring",  # "practice", "scoring", "challenge"
        model_name: Optional[str] = None,
        temperature: float = 0.7,
        api_key: Optional[str] = None,
    ):
        """Initialize enhanced roleplay agent.

        Args:
            persona: PersonaCharacter to roleplay
            difficulty: "beginner", "medium", or "advanced"
            training_mode: "practice", "scoring", or "challenge"
            model_name: Model to use
            temperature: Temperature for generation
            api_key: Anthropic API key
        """
        self.persona = persona
        self.difficulty = difficulty
        self.training_mode = training_mode
        self.scorer = ConversationScorer()

        # Conversation history
        self.conversation_turns: List[Tuple[str, str]] = []  # (agent, client) pairs
        self.turn_scores: List[TurnScore] = []

        # Initialize LLM
        self.llm = ChatAnthropic(
            model=model_name or os.getenv("DEFAULT_MODEL", "claude-sonnet-4-5-20250929"),
            temperature=temperature,
            api_key=api_key or os.getenv("ANTHROPIC_API_KEY"),
        )

        # Message history
        self.message_history: List = []

    def chat(self, agent_message: str, thread_id: Optional[str] = None) -> dict:
        """Send message and get response with scoring.

        Args:
            agent_message: What the agent (trainee) said
            thread_id: Optional thread ID

        Returns:
            Dict with response, score, and feedback
        """
        # Score the agent's message if we have context
        if self.conversation_turns:
            last_client_msg = self.conversation_turns[-1][1] if self.conversation_turns else ""
            turn_score = self.scorer.score_turn(agent_message, context=last_client_msg)
            self.turn_scores.append(turn_score)

            # Adjust persona cooperation based on score
            self.persona.adjust_cooperation(turn_score.total)
        else:
            turn_score = None

        # Get persona response using LangChain
        system_prompt = self.persona.get_system_prompt(self.difficulty)
        messages = [SystemMessage(content=system_prompt)]
        messages.extend(self.message_history)
        messages.append(HumanMessage(content=agent_message))

        # Invoke LLM
        result = self.llm.invoke(messages)
        client_response = result.content

        # Store in message history
        self.message_history.append(HumanMessage(content=agent_message))
        self.message_history.append(AIMessage(content=client_response))

        # Store turn
        self.conversation_turns.append((agent_message, client_response))

        # Prepare response based on training mode
        response = {
            "client_response": client_response,
            "persona_cooperation": self.persona.cooperation_level,
        }

        if self.training_mode == "scoring" and turn_score:
            response["score"] = turn_score.total
            response["max_score"] = turn_score.max_score
            response["feedback"] = turn_score.feedback

        elif self.training_mode == "practice" and turn_score:
            # Show detailed coaching
            response["score"] = turn_score.total
            response["max_score"] = turn_score.max_score
            response["feedback"] = turn_score.feedback
            response["suggested_techniques"] = self._get_suggested_techniques(turn_score)

        # Challenge mode shows no feedback during conversation
        elif self.training_mode == "challenge":
            pass

        return response

    def _get_suggested_techniques(self, turn_score: TurnScore) -> List[str]:
        """Get technique suggestions based on score."""
        suggestions = []

        if turn_score.acknowledge_affirm < 2:
            suggestions.append(
                "Try starting with: 'Perfect!', 'I can appreciate that', or 'That makes sense'"
            )

        if turn_score.isolate < 2:
            suggestions.append(
                "Ask isolation question: 'Besides that, is there any other reason you wouldn't...?'"
            )

        if turn_score.handle < 2:
            suggestions.append(
                "Use Feel-Felt-Found: 'I know how you feel... my clients felt the same... but what they found...'"
            )

        if turn_score.close == 0:
            suggestions.append(
                "Add a close: 'Does that make sense?', 'Which works better for you?'"
            )

        return suggestions

    def get_session_summary(self) -> dict:
        """Get summary of entire session."""
        if not self.turn_scores:
            return {"message": "No turns scored yet"}

        total_score = sum(ts.total for ts in self.turn_scores)
        max_score = sum(ts.max_score for ts in self.turn_scores)
        percentage = (total_score / max_score * 100) if max_score > 0 else 0

        # Calculate averages
        avg_ack = sum(ts.acknowledge_affirm for ts in self.turn_scores) / len(self.turn_scores)
        avg_iso = sum(ts.isolate for ts in self.turn_scores) / len(self.turn_scores)
        avg_handle = sum(ts.handle for ts in self.turn_scores) / len(self.turn_scores)
        avg_close = sum(ts.close for ts in self.turn_scores) / len(self.turn_scores)

        # Identify strengths and improvements
        strengths = []
        improvements = []

        if avg_ack >= 2.5:
            strengths.append("Excellent acknowledgement skills")
        elif avg_ack < 2:
            improvements.append("Work on acknowledgement (start with 'Perfect', 'I appreciate that')")

        if avg_iso >= 2.5:
            strengths.append("Strong objection isolation")
        elif avg_iso < 2:
            improvements.append("Practice isolation questions")

        if avg_handle >= 2.5:
            strengths.append("Good use of handling techniques")
        elif avg_handle < 2:
            improvements.append("Try Feel-Felt-Found or Has There Ever Been techniques")

        # Rapport breakers
        total_breakers = sum(len(ts.rapport_breakers) for ts in self.turn_scores)
        if total_breakers > 0:
            improvements.append(f"Avoid rapport breakers ({total_breakers} detected)")

        # Grade
        if percentage >= 90:
            grade = "A"
        elif percentage >= 80:
            grade = "B"
        elif percentage >= 70:
            grade = "C"
        elif percentage >= 60:
            grade = "D"
        else:
            grade = "F"

        return {
            "total_score": total_score,
            "max_score": max_score,
            "percentage": percentage,
            "grade": grade,
            "num_turns": len(self.turn_scores),
            "averages": {
                "acknowledge_affirm": round(avg_ack, 1),
                "isolate": round(avg_iso, 1),
                "handle": round(avg_handle, 1),
                "close": round(avg_close, 1),
            },
            "strengths": strengths,
            "improvements": improvements,
            "final_cooperation": self.persona.cooperation_level,
        }

    def reset(self):
        """Reset for new session."""
        self.persona.reset_conversation()
        self.conversation_turns = []
        self.turn_scores = []
        self.message_history = []
