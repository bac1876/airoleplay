"""Main entry point for AI Roleplay + Call Coaching System."""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

from airoleplay.characters.persona_character import PersonaCharacter
from airoleplay.agents.enhanced_roleplay_agent import EnhancedRoleplayAgent
from airoleplay.call_analysis.audio_processor import AudioProcessor
from airoleplay.call_analysis.call_analyzer import CallAnalyzer


def print_header():
    """Print application header."""
    print("\n" + "=" * 70)
    print("AI ROLEPLAY + CALL COACHING SYSTEM")
    print("Real Estate Sales Training with CFR Framework")
    print("=" * 70 + "\n")


def print_menu():
    """Print main menu."""
    print("\n--- MAIN MENU ---")
    print("1. Live Roleplay Training")
    print("2. Analyze Call Recording")
    print("3. View Personas")
    print("4. Exit")
    print()


def select_persona() -> PersonaCharacter:
    """Let user select a persona."""
    personas_dir = Path(__file__).parent / "airoleplay" / "personas"

    personas = {
        "1": ("investor.json", "Investor – Cash Flow Focused"),
        "2": ("first_time_buyer.json", "First Time Buyer – Anxious/Curious"),
        "3": ("seller.json", "Seller / Downsizer – Convenience & Timing")
    }

    print("\n--- SELECT PERSONA ---")
    for key, (_, label) in personas.items():
        print(f"{key}. {label}")

    while True:
        choice = input("\nSelect persona (1-3): ").strip()
        if choice in personas:
            filename, _ = personas[choice]
            persona_path = personas_dir / filename
            return PersonaCharacter.from_json(str(persona_path))
        print("Invalid choice. Please select 1-3.")


def select_difficulty() -> str:
    """Let user select difficulty level."""
    print("\n--- SELECT DIFFICULTY ---")
    print("1. Beginner (2 easy objections)")
    print("2. Medium (4 moderate objections)")
    print("3. Advanced (All objections)")

    while True:
        choice = input("\nSelect difficulty (1-3): ").strip()
        if choice == "1":
            return "beginner"
        elif choice == "2":
            return "medium"
        elif choice == "3":
            return "advanced"
        print("Invalid choice. Please select 1-3.")


def select_training_mode() -> str:
    """Let user select training mode."""
    print("\n--- SELECT TRAINING MODE ---")
    print("1. Practice Mode (detailed coaching after each turn)")
    print("2. Scoring Mode (realtime score feedback)")
    print("3. Challenge Mode (no feedback until end)")

    while True:
        choice = input("\nSelect mode (1-3): ").strip()
        if choice == "1":
            return "practice"
        elif choice == "2":
            return "scoring"
        elif choice == "3":
            return "challenge"
        print("Invalid choice. Please select 1-3.")


def live_roleplay_training():
    """Run live roleplay training session."""
    print("\n" + "=" * 70)
    print("LIVE ROLEPLAY TRAINING")
    print("=" * 70)

    # Setup
    persona = select_persona()
    difficulty = select_difficulty()
    training_mode = select_training_mode()

    print(f"\n✓ Persona: {persona.label}")
    print(f"✓ Difficulty: {difficulty.title()}")
    print(f"✓ Mode: {training_mode.title()}")
    print("\nInitializing agent...")

    agent = EnhancedRoleplayAgent(
        persona=persona,
        difficulty=difficulty,
        training_mode=training_mode
    )

    # Conversation loop
    print("\n" + "=" * 70)
    print(f"CONVERSATION WITH {persona.label.upper()}")
    print("=" * 70)
    print("\nType your responses as a real estate agent.")
    print("Type 'end' to finish session and see summary.")
    print("=" * 70 + "\n")

    # Initial message from persona
    initial_response = agent.chat(
        "Hi, I'm a real estate agent. How can I help you today?",
        thread_id="training_session"
    )

    print(f"{persona.label}: {initial_response['client_response']}\n")
    if training_mode == "scoring":
        print(f"[Cooperation: {initial_response['persona_cooperation']}/10]\n")

    turn_num = 1

    while True:
        try:
            # Get agent (trainee) response
            agent_input = input(f"You (Turn {turn_num}): ").strip()

            if not agent_input:
                continue

            if agent_input.lower() == "end":
                break

            # Process response
            response = agent.chat(agent_input, thread_id="training_session")

            # Show persona response
            print(f"\n{persona.label}: {response['client_response']}")

            # Show feedback based on mode
            if training_mode == "practice" and "score" in response:
                print(f"\n--- TURN {turn_num} FEEDBACK ---")
                print(f"Score: {response['score']}/{response['max_score']}")
                if response.get("feedback"):
                    for fb in response["feedback"]:
                        print(f"  {fb}")
                if response.get("suggested_techniques"):
                    print("\n💡 Suggested techniques:")
                    for st in response["suggested_techniques"]:
                        print(f"  • {st}")
                print()

            elif training_mode == "scoring" and "score" in response:
                print(f"[Score: {response['score']}/{response['max_score']} | Cooperation: {response['persona_cooperation']}/10]\n")

            turn_num += 1

        except KeyboardInterrupt:
            print("\n\nSession interrupted.")
            break
        except Exception as e:
            print(f"\nError: {e}")
            print("Continuing...\n")

    # Show session summary
    print("\n" + "=" * 70)
    print("SESSION SUMMARY")
    print("=" * 70)

    summary = agent.get_session_summary()

    if "message" in summary:
        print(summary["message"])
    else:
        print(f"\nOverall Score: {summary['total_score']}/{summary['max_score']} ({summary['percentage']:.1f}%) - Grade: {summary['grade']}")
        print(f"Turns: {summary['num_turns']}")
        print(f"\nAverage Scores:")
        print(f"  Acknowledge/Affirm: {summary['averages']['acknowledge_affirm']}/3")
        print(f"  Isolate: {summary['averages']['isolate']}/3")
        print(f"  Handle: {summary['averages']['handle']}/3")
        print(f"  Close: {summary['averages']['close']}/2")

        if summary['strengths']:
            print(f"\n✓ STRENGTHS:")
            for strength in summary['strengths']:
                print(f"  • {strength}")

        if summary['improvements']:
            print(f"\n⚠️  IMPROVEMENTS:")
            for improvement in summary['improvements']:
                print(f"  • {improvement}")

        print(f"\nFinal Persona Cooperation: {summary['final_cooperation']}/10")

    print("\n" + "=" * 70)


def analyze_call_recording():
    """Analyze uploaded call recording."""
    print("\n" + "=" * 70)
    print("CALL RECORDING ANALYSIS")
    print("=" * 70)

    # Check for OpenAI API key
    if not os.getenv("OPENAI_API_KEY"):
        print("\n⚠️  Error: OPENAI_API_KEY not found in environment variables.")
        print("Call analysis requires OpenAI API for Whisper transcription.")
        print("Please add OPENAI_API_KEY to your .env file.")
        return

    # Get file path
    audio_file = input("\nEnter path to audio file (MP3, WAV, M4A): ").strip()
    audio_path = Path(audio_file)

    if not audio_path.exists():
        print(f"\n⚠️  Error: File not found: {audio_file}")
        return

    print("\nProcessing call...")
    print("=" * 70)

    try:
        # Process audio
        processor = AudioProcessor()
        transcript = processor.process_call_file(str(audio_path))

        # Analyze
        analyzer = CallAnalyzer()
        report = analyzer.analyze_call(transcript)

        # Display report
        print("\n" + str(report))

        # Offer to save
        save = input("\nSave detailed report to file? (y/n): ").strip().lower()
        if save == "y":
            output_dir = Path("call_reports")
            output_dir.mkdir(exist_ok=True)
            report_path = output_dir / f"{audio_path.stem}_report.txt"

            with open(report_path, 'w', encoding='utf-8') as f:
                f.write(str(report))
                f.write("\n\n" + "=" * 70)
                f.write("\nDETAILED TURN-BY-TURN FEEDBACK")
                f.write("\n" + "=" * 70 + "\n")

                for i, (score, feedback) in enumerate(zip(report.turn_scores, report.timestamped_feedback)):
                    f.write(f"\nTurn {i+1}:")
                    f.write(f"\n  Score: {score.total}/{score.max_score}")
                    f.write(f"\n  Feedback: {feedback.message}")
                    if feedback.suggested_technique:
                        f.write(f"\n  Suggested: {feedback.suggested_technique}")
                    f.write("\n")

            print(f"\n✓ Report saved to: {report_path}")

    except Exception as e:
        print(f"\n⚠️  Error processing call: {e}")
        import traceback
        traceback.print_exc()


def view_personas():
    """Display available personas."""
    personas_dir = Path(__file__).parent / "airoleplay" / "personas"

    print("\n" + "=" * 70)
    print("AVAILABLE PERSONAS")
    print("=" * 70)

    personas = [
        ("investor.json", "Investor – Cash Flow Focused"),
        ("first_time_buyer.json", "First Time Buyer – Anxious/Curious"),
        ("seller.json", "Seller / Downsizer – Convenience & Timing")
    ]

    for filename, label in personas:
        persona_path = personas_dir / filename
        persona = PersonaCharacter.from_json(str(persona_path))

        print(f"\n{label}")
        print("-" * 70)
        print(f"Traits: {', '.join(persona.persona_traits)}")
        print(f"Context: {persona.context}")
        print(f"Objections: {len(persona.objection_patterns)} patterns")
        print(f"Goals: {', '.join(persona.goals[:3])}")

    print("\n" + "=" * 70)


def main():
    """Main application loop."""
    # Load environment variables
    load_dotenv()

    # Check for API keys
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("\n⚠️  Warning: ANTHROPIC_API_KEY not found in environment variables.")
        print("Please create a .env file with your API key (see .env.example)")
        print("Live roleplay training will not work without it.\n")

    print_header()

    while True:
        print_menu()

        choice = input("Select option (1-4): ").strip()

        if choice == "1":
            if not os.getenv("ANTHROPIC_API_KEY"):
                print("\n⚠️  Error: ANTHROPIC_API_KEY required for roleplay training.")
                continue
            live_roleplay_training()

        elif choice == "2":
            analyze_call_recording()

        elif choice == "3":
            view_personas()

        elif choice == "4":
            print("\nGoodbye! Keep practicing those CFR techniques! 🎯\n")
            break

        else:
            print("\nInvalid choice. Please select 1-4.")


if __name__ == "__main__":
    main()
