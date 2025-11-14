"""CFR-based conversation scoring and analysis."""

import re
import json
from typing import Dict, List, Tuple, Optional
from pathlib import Path
from dataclasses import dataclass, field


@dataclass
class TurnScore:
    """Score for a single conversation turn."""
    acknowledge_affirm: int = 0  # 0-3
    isolate: int = 0  # 0-3
    handle: int = 0  # 0-3
    close: int = 0  # 0-2
    magic_phrases_used: List[str] = field(default_factory=list)
    techniques_detected: List[str] = field(default_factory=list)
    rapport_breakers: List[str] = field(default_factory=list)
    feedback: List[str] = field(default_factory=list)

    @property
    def total(self) -> int:
        """Calculate total score."""
        return self.acknowledge_affirm + self.isolate + self.handle + self.close

    @property
    def max_score(self) -> int:
        """Maximum possible score."""
        return 11  # 3+3+3+2


@dataclass
class ConversationScore:
    """Overall conversation score."""
    turns: List[TurnScore] = field(default_factory=list)
    overall_feedback: List[str] = field(default_factory=list)

    @property
    def total_score(self) -> int:
        """Sum of all turn scores."""
        return sum(turn.total for turn in self.turns)

    @property
    def max_possible_score(self) -> int:
        """Maximum possible score for all turns."""
        return sum(turn.max_score for turn in self.turns)

    @property
    def percentage(self) -> float:
        """Score as percentage."""
        if self.max_possible_score == 0:
            return 0.0
        return (self.total_score / self.max_possible_score) * 100

    @property
    def grade(self) -> str:
        """Letter grade."""
        pct = self.percentage
        if pct >= 90:
            return "A"
        elif pct >= 80:
            return "B"
        elif pct >= 70:
            return "C"
        elif pct >= 60:
            return "D"
        else:
            return "F"


class ConversationScorer:
    """Scores conversations based on CFR framework."""

    def __init__(self):
        """Initialize scorer with technique patterns."""
        # Load techniques and magic phrases
        data_dir = Path(__file__).parent.parent / "data"

        with open(data_dir / "techniques.json", 'r') as f:
            self.techniques = json.load(f)

        with open(data_dir / "magic_phrases.json", 'r') as f:
            self.magic_phrases = json.load(f)

        # Compile patterns
        self._compile_patterns()

    def _compile_patterns(self):
        """Compile regex patterns for detection."""
        # Acknowledgement terms
        self.acknowledge_terms = [
            "perfect", "that makes perfect sense", "absolutely", "great",
            "fantastic", "you're absolutely right", "that's valid", "you're right",
            "i can appreciate that", "i understand your concern", "amazing",
            "most people tell me that", "i can see the benefit", "wonderful"
        ]

        # Rapport breakers (exact match needed)
        self.rapport_breakers = {
            r"\bi understand\b(?! your concern)": "Used 'I understand' without qualifier - breaks rapport",
            r"\byou'?re wrong\b": "Told client they're wrong - breaks rapport",
            r"\bactually\b": "Used 'actually' - can sound argumentative",
            r"\bbut you said\b": "Contradicted client - breaks rapport"
        }

        # Isolation questions
        self.isolation_patterns = [
            r"besides .+, is there any",
            r"other than .+, is there",
            r"out of curiosity, what",
            r"what is the benefit",
            r"what specifically makes you",
            r"any other reason you wouldn't"
        ]

        # Closing patterns
        self.closing_patterns = [
            r"which works better",
            r"does that (make sense|sound good|work for you)",
            r"would you like to",
            r"why don't we",
            r"let's",
            r"can you see",
            r"please sign"
        ]

        # Feel-Felt-Found pattern
        self.feel_felt_found_pattern = r"(how you feel|you felt|they found)"

        # Has there ever been pattern
        self.has_there_ever_pattern = r"has there ever been a time"

    def score_turn(self, agent_message: str, context: Optional[str] = None) -> TurnScore:
        """Score a single agent response.

        Args:
            agent_message: What the agent said
            context: Optional context (what client said before)

        Returns:
            TurnScore with detailed feedback
        """
        score = TurnScore()
        agent_lower = agent_message.lower()

        # 1. ACKNOWLEDGE & AFFIRM (0-3 points)
        ack_score, ack_feedback = self._score_acknowledge_affirm(agent_lower)
        score.acknowledge_affirm = ack_score
        score.feedback.extend(ack_feedback)

        # 2. ISOLATE (0-3 points)
        iso_score, iso_feedback = self._score_isolate(agent_lower)
        score.isolate = iso_score
        score.feedback.extend(iso_feedback)

        # 3. HANDLE (0-3 points)
        handle_score, handle_feedback = self._score_handle(agent_lower, agent_message)
        score.handle = handle_score
        score.feedback.extend(handle_feedback)
        score.techniques_detected.extend([fb for fb in handle_feedback if "technique" in fb.lower()])

        # 4. CLOSE (0-2 points)
        close_score, close_feedback = self._score_close(agent_lower)
        score.close = close_score
        score.feedback.extend(close_feedback)

        # Detect magic phrases
        score.magic_phrases_used = self._detect_magic_phrases(agent_lower)

        # Detect rapport breakers (NEGATIVE points)
        score.rapport_breakers = self._detect_rapport_breakers(agent_lower)
        if score.rapport_breakers:
            # Penalize total score
            penalty = len(score.rapport_breakers)
            score.feedback.append(f"⚠️ Rapport breakers detected: -{penalty} points")

        return score

    def _score_acknowledge_affirm(self, agent_lower: str) -> Tuple[int, List[str]]:
        """Score acknowledge & affirm step (0-3 points)."""
        score = 0
        feedback = []

        # Check for acknowledgement terms
        found_terms = [term for term in self.acknowledge_terms if term in agent_lower]

        if len(found_terms) >= 2:
            score = 3
            feedback.append(f"✓ Excellent acknowledgement: used '{found_terms[0]}' and '{found_terms[1]}'")
        elif len(found_terms) == 1:
            score = 2
            feedback.append(f"✓ Good acknowledgement: used '{found_terms[0]}'")
        else:
            score = 0
            feedback.append("⚠️ Missing acknowledgement - start with 'Perfect', 'I can appreciate that', etc.")

        return score, feedback

    def _score_isolate(self, agent_lower: str) -> Tuple[int, List[str]]:
        """Score isolation step (0-3 points)."""
        score = 0
        feedback = []

        # Check for isolation questions
        matches = [p for p in self.isolation_patterns if re.search(p, agent_lower)]

        if len(matches) >= 2:
            score = 3
            feedback.append("✓ Excellent isolation: asked multiple clarifying questions")
        elif len(matches) == 1:
            score = 2
            feedback.append("✓ Good isolation: asked clarifying question")
        else:
            score = 0
            feedback.append("⚠️ Missing isolation - ask 'Besides that, is there any other reason you wouldn't...?'")

        return score, feedback

    def _score_handle(self, agent_lower: str, agent_full: str) -> Tuple[int, List[str]]:
        """Score handling step (0-3 points)."""
        score = 0
        feedback = []
        techniques_found = []

        # Check for Feel-Felt-Found
        if re.search(self.feel_felt_found_pattern, agent_lower):
            score += 2
            techniques_found.append("Feel-Felt-Found technique")
            feedback.append("✓ Used Feel-Felt-Found empathy technique")

        # Check for Has There Ever Been
        if re.search(self.has_there_ever_pattern, agent_lower):
            score += 2
            techniques_found.append("Has There Ever Been technique")
            feedback.append("✓ Used 'Has There Ever Been' pattern - leveraging past mistakes")

        # Check for Level Shift phrases
        level_shift_phrases = [
            "what i think you're saying", "the real issue", "what appears most important",
            "what i sense", "i believe you're asking", "what i hear you saying"
        ]
        if any(phrase in agent_lower for phrase in level_shift_phrases):
            score += 1
            techniques_found.append("Level Shift")
            feedback.append("✓ Used Level Shift to reframe")

        # Check for embedded commands (ALL CAPS words)
        embedded = re.findall(r'\b[A-Z]{2,}(?:\s+[A-Z]{2,})*\b', agent_full)
        if embedded and len(embedded) > 0:
            score += 1
            feedback.append(f"✓ Used embedded command: {embedded[0]}")

        # If no techniques detected
        if score == 0:
            score = 1  # Basic handling
            feedback.append("⚠️ Consider using Feel-Felt-Found or Has There Ever Been technique")

        # Cap at 3
        score = min(3, score)

        return score, feedback

    def _score_close(self, agent_lower: str) -> Tuple[int, List[str]]:
        """Score closing step (0-2 points)."""
        score = 0
        feedback = []

        # Check for closing patterns
        matches = [p for p in self.closing_patterns if re.search(p, agent_lower)]

        if len(matches) >= 2:
            score = 2
            feedback.append("✓ Strong close: multiple closing questions/statements")
        elif len(matches) == 1:
            score = 1
            feedback.append("✓ Attempted close")
        else:
            score = 0
            feedback.append("⚠️ Missing close - try 'Does that make sense?', 'Which works better for you?'")

        return score, feedback

    def _detect_magic_phrases(self, agent_lower: str) -> List[str]:
        """Detect which magic phrases were used."""
        used = []

        for phrase_key, phrase_data in self.magic_phrases["magic_phrases"].items():
            # Check if any example patterns match
            if "pattern" in phrase_data:
                # Simple pattern matching
                pattern_keywords = phrase_data["pattern"].lower().split()
                if any(keyword in agent_lower for keyword in pattern_keywords[:3]):
                    used.append(phrase_data["name"])

        return used

    def _detect_rapport_breakers(self, agent_lower: str) -> List[str]:
        """Detect rapport-breaking phrases."""
        breakers = []

        for pattern, message in self.rapport_breakers.items():
            if re.search(pattern, agent_lower):
                breakers.append(message)

        return breakers

    def score_conversation(self, conversation_turns: List[Tuple[str, str]]) -> ConversationScore:
        """Score an entire conversation.

        Args:
            conversation_turns: List of (agent_message, client_message) tuples

        Returns:
            ConversationScore with all turns and overall feedback
        """
        conv_score = ConversationScore()

        for i, (agent_msg, client_msg) in enumerate(conversation_turns):
            turn_score = self.score_turn(agent_msg, context=client_msg)
            conv_score.turns.append(turn_score)

        # Generate overall feedback
        conv_score.overall_feedback = self._generate_overall_feedback(conv_score)

        return conv_score

    def _generate_overall_feedback(self, conv_score: ConversationScore) -> List[str]:
        """Generate coaching feedback for entire conversation."""
        feedback = []

        # Overall performance
        feedback.append(f"Overall Score: {conv_score.total_score}/{conv_score.max_possible_score} ({conv_score.percentage:.1f}%) - Grade: {conv_score.grade}")

        # Strengths
        strengths = []
        avg_ack = sum(t.acknowledge_affirm for t in conv_score.turns) / max(len(conv_score.turns), 1)
        avg_iso = sum(t.isolate for t in conv_score.turns) / max(len(conv_score.turns), 1)

        if avg_ack >= 2.5:
            strengths.append("Excellent at acknowledging and affirming")
        if avg_iso >= 2.5:
            strengths.append("Strong isolation skills")

        if strengths:
            feedback.append(f"\n✓ Strengths: {', '.join(strengths)}")

        # Areas for improvement
        improvements = []
        if avg_ack < 2:
            improvements.append("Work on acknowledging client concerns first")
        if avg_iso < 2:
            improvements.append("Practice isolation questions more")

        # Count rapport breakers
        total_breakers = sum(len(t.rapport_breakers) for t in conv_score.turns)
        if total_breakers > 0:
            improvements.append(f"Avoid rapport breakers ({total_breakers} detected)")

        if improvements:
            feedback.append(f"\n⚠️ Areas to improve: {', '.join(improvements)}")

        # Technique recommendations
        all_techniques = []
        for turn in conv_score.turns:
            all_techniques.extend(turn.techniques_detected)

        if not all_techniques:
            feedback.append("\n💡 Try using: Feel-Felt-Found, Has There Ever Been, or Level Shift techniques")

        return feedback
