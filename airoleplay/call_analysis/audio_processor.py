"""Audio processing for call uploads using Whisper."""

import os
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass

try:
    import openai
except ImportError:
    openai = None


@dataclass
class TranscriptSegment:
    """A segment of transcribed audio."""
    start: float
    end: float
    text: str
    speaker: Optional[str] = None  # "agent" or "client"


@dataclass
class CallTranscript:
    """Complete transcript of a call."""
    segments: List[TranscriptSegment]
    duration: float
    language: str = "en"

    def get_turns(self) -> List[tuple[str, str, float]]:
        """Get conversation turns as (speaker, text, timestamp) tuples."""
        turns = []
        for seg in self.segments:
            turns.append((seg.speaker or "unknown", seg.text, seg.start))
        return turns

    def get_agent_turns(self) -> List[tuple[str, float]]:
        """Get only agent turns as (text, timestamp) tuples."""
        return [(seg.text, seg.start) for seg in self.segments if seg.speaker == "agent"]

    def get_client_turns(self) -> List[tuple[str, float]]:
        """Get only client turns as (text, timestamp) tuples."""
        return [(seg.text, seg.start) for seg in self.segments if seg.speaker == "client"]


class AudioProcessor:
    """Process audio files for call coaching."""

    def __init__(self, api_key: Optional[str] = None):
        """Initialize audio processor.

        Args:
            api_key: OpenAI API key (or uses OPENAI_API_KEY env var)
        """
        if openai is None:
            raise ImportError(
                "OpenAI package not installed. Run: pip install openai"
            )

        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError(
                "OpenAI API key required. Set OPENAI_API_KEY env var or pass api_key parameter"
            )

        self.client = openai.OpenAI(api_key=self.api_key)

    def transcribe_audio(
        self,
        audio_file_path: str,
        language: str = "en",
        prompt: Optional[str] = None
    ) -> CallTranscript:
        """Transcribe audio file using Whisper.

        Args:
            audio_file_path: Path to audio file (MP3, WAV, M4A, etc.)
            language: Language code (default: "en")
            prompt: Optional prompt to guide transcription

        Returns:
            CallTranscript with segments
        """
        audio_path = Path(audio_file_path)
        if not audio_path.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_file_path}")

        print(f"Transcribing {audio_path.name}...")

        # Transcribe with Whisper
        with open(audio_path, 'rb') as audio_file:
            transcript = self.client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                language=language,
                response_format="verbose_json",  # Get timestamps
                prompt=prompt or "This is a real estate sales call between an agent and a client discussing buying or selling property."
            )

        # Extract segments
        segments = []
        if hasattr(transcript, 'segments') and transcript.segments:
            for seg in transcript.segments:
                segments.append(TranscriptSegment(
                    start=seg['start'],
                    end=seg['end'],
                    text=seg['text'].strip()
                ))
        else:
            # Fallback if no segments
            segments.append(TranscriptSegment(
                start=0.0,
                end=0.0,
                text=transcript.text
            ))

        # Get duration
        duration = segments[-1].end if segments else 0.0

        print(f"✓ Transcription complete: {len(segments)} segments, {duration:.1f}s")

        return CallTranscript(
            segments=segments,
            duration=duration,
            language=language
        )

    def identify_speakers(
        self,
        transcript: CallTranscript,
        agent_keywords: Optional[List[str]] = None
    ) -> CallTranscript:
        """Identify speakers in transcript using simple heuristics.

        Args:
            transcript: CallTranscript to analyze
            agent_keywords: Keywords that suggest agent speech (e.g., ["i can help", "let me show"])

        Returns:
            Updated CallTranscript with speaker labels
        """
        if agent_keywords is None:
            agent_keywords = [
                "let me show you",
                "i can help",
                "our team",
                "i would recommend",
                "i'll send you",
                "my clients",
                "i appreciate that",
                "perfect",
                "does that make sense"
            ]

        print("Identifying speakers...")

        for i, seg in enumerate(transcript.segments):
            text_lower = seg.text.lower()

            # Simple heuristic: check for agent keywords
            is_agent = any(keyword in text_lower for keyword in agent_keywords)

            # Alternate speakers (simple assumption)
            if i == 0:
                # First speaker - check keywords
                seg.speaker = "agent" if is_agent else "client"
            else:
                prev_speaker = transcript.segments[i-1].speaker
                # If strong agent keyword, mark as agent
                if is_agent:
                    seg.speaker = "agent"
                # Otherwise alternate
                else:
                    seg.speaker = "client" if prev_speaker == "agent" else "agent"

        agent_count = sum(1 for seg in transcript.segments if seg.speaker == "agent")
        client_count = len(transcript.segments) - agent_count

        print(f"✓ Identified {agent_count} agent turns, {client_count} client turns")

        return transcript

    def save_transcript(self, transcript: CallTranscript, output_path: str):
        """Save transcript to text file.

        Args:
            transcript: CallTranscript to save
            output_path: Output file path
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(f"Call Transcript ({transcript.duration:.1f}s)\n")
            f.write("=" * 60 + "\n\n")

            for seg in transcript.segments:
                timestamp = f"[{seg.start:.1f}s]"
                speaker = seg.speaker.upper() if seg.speaker else "UNKNOWN"
                f.write(f"{timestamp} {speaker}: {seg.text}\n")

        print(f"✓ Transcript saved to {output_path}")

    def process_call_file(
        self,
        audio_file_path: str,
        save_transcript_path: Optional[str] = None
    ) -> CallTranscript:
        """Complete processing pipeline for a call file.

        Args:
            audio_file_path: Path to audio file
            save_transcript_path: Optional path to save transcript

        Returns:
            CallTranscript with speaker identification
        """
        # Transcribe
        transcript = self.transcribe_audio(audio_file_path)

        # Identify speakers
        transcript = self.identify_speakers(transcript)

        # Save if requested
        if save_transcript_path:
            self.save_transcript(transcript, save_transcript_path)

        return transcript
