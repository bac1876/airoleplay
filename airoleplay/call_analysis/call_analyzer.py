"""Analyze call transcripts and generate coaching reports."""

from typing import List, Tuple, Optional, Dict
from dataclasses import dataclass, field
from pathlib import Path

from ..scoring.conversation_scorer import ConversationScorer, TurnScore
from .audio_processor import CallTranscript


@dataclass
class TimestampedFeedback:
    """Feedback for a specific moment in the call."""
    timestamp: float
    turn_number: int
    feedback_type: str  # "strength", "improvement", "critical"
    message: str
    suggested_technique: Optional[str] = None
    example_script: Optional[str] = None


@dataclass
class CallAnalysisReport:
    """Complete analysis report for a call."""
    transcript: CallTranscript
    turn_scores: List[TurnScore]
    overall_score: int
    max_score: int
    percentage: float
    grade: str
    timestamped_feedback: List[TimestampedFeedback]
    key_wins: List[str]
    improvement_areas: List[str]
    technique_recommendations: List[str]
    missed_opportunities: List[Dict[str, str]]

    def __str__(self) -> str:
        """Generate text report."""
        lines = []
        lines.append("=" * 70)
        lines.append(" CALL COACHING REPORT")
        lines.append("=" * 70)
        lines.append(f"\nOverall Score: {self.overall_score}/{self.max_score} ({self.percentage:.1f}%) - Grade: {self.grade}\n")

        if self.key_wins:
            lines.append("\n✓ KEY WINS:")
            for win in self.key_wins:
                lines.append(f"  • {win}")

        if self.improvement_areas:
            lines.append("\n⚠️  AREAS FOR IMPROVEMENT:")
            for area in self.improvement_areas:
                lines.append(f"  • {area}")

        if self.technique_recommendations:
            lines.append("\n💡 TECHNIQUE RECOMMENDATIONS:")
            for rec in self.technique_recommendations:
                lines.append(f"  • {rec}")

        if self.missed_opportunities:
            lines.append("\n🎯 MISSED OPPORTUNITIES:")
            for opp in self.missed_opportunities:
                lines.append(f"\n  [{opp['timestamp']}] {opp['context']}")
                lines.append(f"    → Suggested: {opp['suggestion']}")
                if 'example' in opp:
                    lines.append(f"    → Example: {opp['example']}")

        lines.append("\n" + "=" * 70)
        return "\n".join(lines)


class CallAnalyzer:
    """Analyze call transcripts for coaching."""

    def __init__(self):
        """Initialize call analyzer."""
        self.scorer = ConversationScorer()

    def analyze_call(self, transcript: CallTranscript) -> CallAnalysisReport:
        """Analyze a call transcript.

        Args:
            transcript: CallTranscript with speaker labels

        Returns:
            CallAnalysisReport with detailed coaching
        """
        print("Analyzing call...")

        # Extract conversation turns (agent, client pairs)
        turns = self._extract_turns(transcript)

        # Score each agent turn
        turn_scores = []
        for i, (agent_msg, client_msg) in enumerate(turns):
            score = self.scorer.score_turn(agent_msg, context=client_msg)
            turn_scores.append(score)

        # Calculate overall metrics
        total_score = sum(ts.total for ts in turn_scores)
        max_score = sum(ts.max_score for ts in turn_scores)
        percentage = (total_score / max_score * 100) if max_score > 0 else 0

        # Assign grade
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

        # Generate timestamped feedback
        timestamped_feedback = self._generate_timestamped_feedback(
            transcript, turns, turn_scores
        )

        # Extract key insights
        key_wins = self._identify_key_wins(turn_scores)
        improvement_areas = self._identify_improvements(turn_scores)
        technique_recommendations = self._recommend_techniques(turn_scores)
        missed_opportunities = self._find_missed_opportunities(transcript, turns, turn_scores)

        print(f"✓ Analysis complete: {total_score}/{max_score} ({percentage:.1f}%)")

        return CallAnalysisReport(
            transcript=transcript,
            turn_scores=turn_scores,
            overall_score=total_score,
            max_score=max_score,
            percentage=percentage,
            grade=grade,
            timestamped_feedback=timestamped_feedback,
            key_wins=key_wins,
            improvement_areas=improvement_areas,
            technique_recommendations=technique_recommendations,
            missed_opportunities=missed_opportunities
        )

    def _extract_turns(self, transcript: CallTranscript) -> List[Tuple[str, str]]:
        """Extract (agent, client) conversation pairs."""
        turns = []
        agent_turns = transcript.get_agent_turns()
        client_turns = transcript.get_client_turns()

        # Pair agent responses with preceding client messages
        for i, (agent_text, agent_time) in enumerate(agent_turns):
            # Find most recent client message before this agent response
            client_text = ""
            for client_msg, client_time in client_turns:
                if client_time < agent_time:
                    client_text = client_msg
                else:
                    break

            turns.append((agent_text, client_text))

        return turns

    def _generate_timestamped_feedback(
        self,
        transcript: CallTranscript,
        turns: List[Tuple[str, str]],
        scores: List[TurnScore]
    ) -> List[TimestampedFeedback]:
        """Generate feedback tied to specific timestamps."""
        feedback_list = []

        agent_turns = transcript.get_agent_turns()

        for i, (score, (agent_msg, client_msg)) in enumerate(zip(scores, turns)):
            timestamp = agent_turns[i][1] if i < len(agent_turns) else 0.0

            # Critical issues
            if score.rapport_breakers:
                for breaker in score.rapport_breakers:
                    feedback_list.append(TimestampedFeedback(
                        timestamp=timestamp,
                        turn_number=i+1,
                        feedback_type="critical",
                        message=f"Rapport breaker: {breaker}",
                        suggested_technique="Use 'I can appreciate that' instead of 'I understand'"
                    ))

            # Low isolation score
            if score.isolate < 2:
                feedback_list.append(TimestampedFeedback(
                    timestamp=timestamp,
                    turn_number=i+1,
                    feedback_type="improvement",
                    message="Client raised objection but you didn't isolate",
                    suggested_technique="Ask: 'Besides that, is there any other reason you wouldn't...?'"
                ))

            # Strong performance
            if score.total >= 9:
                feedback_list.append(TimestampedFeedback(
                    timestamp=timestamp,
                    turn_number=i+1,
                    feedback_type="strength",
                    message=f"Excellent CFR technique usage! Score: {score.total}/11"
                ))

        return feedback_list

    def _identify_key_wins(self, scores: List[TurnScore]) -> List[str]:
        """Identify what the agent did well."""
        wins = []

        # Count strong techniques
        high_scoring_turns = [s for s in scores if s.total >= 8]
        if len(high_scoring_turns) > len(scores) / 2:
            wins.append("Consistent use of CFR framework throughout call")

        # Check acknowledgement
        avg_ack = sum(s.acknowledge_affirm for s in scores) / max(len(scores), 1)
        if avg_ack >= 2.5:
            wins.append("Excellent acknowledgement and affirmation skills")

        # Check isolation
        avg_iso = sum(s.isolate for s in scores) / max(len(scores), 1)
        if avg_iso >= 2.5:
            wins.append("Strong objection isolation")

        # Check for advanced techniques
        all_techniques = []
        for score in scores:
            all_techniques.extend(score.techniques_detected)

        if "Feel-Felt-Found" in " ".join(all_techniques):
            wins.append("Used Feel-Felt-Found empathy technique")

        if len(all_techniques) >= 3:
            wins.append(f"Demonstrated variety of techniques ({len(set(all_techniques))} different)")

        return wins

    def _identify_improvements(self, scores: List[TurnScore]) -> List[str]:
        """Identify areas needing improvement."""
        improvements = []

        # Check averages
        avg_ack = sum(s.acknowledge_affirm for s in scores) / max(len(scores), 1)
        avg_iso = sum(s.isolate for s in scores) / max(len(scores), 1)
        avg_handle = sum(s.handle for s in scores) / max(len(scores), 1)
        avg_close = sum(s.close for s in scores) / max(len(scores), 1)

        if avg_ack < 2:
            improvements.append("Start responses with acknowledgement ('Perfect', 'I can appreciate that')")

        if avg_iso < 2:
            improvements.append("Practice isolation questions ('Besides that, any other concerns?')")

        if avg_handle < 2:
            improvements.append("Use more advanced techniques (Feel-Felt-Found, Level Shift)")

        if avg_close < 1:
            improvements.append("Add closing questions ('Does that make sense?', 'Which works better?')")

        # Rapport breakers
        total_breakers = sum(len(s.rapport_breakers) for s in scores)
        if total_breakers > 0:
            improvements.append(f"Avoid rapport breakers ({total_breakers} instances detected)")

        return improvements

    def _recommend_techniques(self, scores: List[TurnScore]) -> List[str]:
        """Recommend specific techniques to practice."""
        recommendations = []

        # Check what techniques are missing
        all_techniques = []
        for score in scores:
            all_techniques.extend(score.techniques_detected)

        if "Feel-Felt-Found" not in " ".join(all_techniques):
            recommendations.append(
                "Try Feel-Felt-Found: 'I know how you FEEL... clients have FELT the same... "
                "but what they FOUND was...'"
            )

        if "Has There Ever Been" not in " ".join(all_techniques):
            recommendations.append(
                "Use 'Has There Ever Been': Leverage past mistakes to prevent new ones"
            )

        # Check isolation
        low_isolation_count = sum(1 for s in scores if s.isolate < 2)
        if low_isolation_count > len(scores) / 2:
            recommendations.append(
                "Practice isolation: 'Besides X, is there any other reason you wouldn't Y?'"
            )

        return recommendations

    def _find_missed_opportunities(
        self,
        transcript: CallTranscript,
        turns: List[Tuple[str, str]],
        scores: List[TurnScore]
    ) -> List[Dict[str, str]]:
        """Find specific moments where better techniques could have been used."""
        opportunities = []

        agent_turns = transcript.get_agent_turns()

        for i, (score, (agent_msg, client_msg)) in enumerate(zip(scores, turns)):
            timestamp = agent_turns[i][1] if i < len(agent_turns) else 0.0

            # Missed isolation
            if score.isolate == 0 and client_msg:
                opportunities.append({
                    "timestamp": f"{timestamp:.1f}s",
                    "context": f"Client said: '{client_msg[:50]}...'",
                    "suggestion": "Isolate the objection",
                    "example": f"Besides that, is there any other reason you wouldn't move forward?"
                })

            # No acknowledgement
            if score.acknowledge_affirm == 0:
                opportunities.append({
                    "timestamp": f"{timestamp:.1f}s",
                    "context": "Response started without acknowledgement",
                    "suggestion": "Start with acknowledgement term",
                    "example": "Perfect! I can appreciate that concern..."
                })

        return opportunities[:5]  # Limit to top 5
