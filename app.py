"""Streamlit web interface for AI Roleplay + Call Coaching System."""

import os
import streamlit as st
from pathlib import Path
from dotenv import load_dotenv
import tempfile

from airoleplay.characters.persona_character import PersonaCharacter
from airoleplay.agents.enhanced_roleplay_agent import EnhancedRoleplayAgent
from airoleplay.call_analysis.audio_processor import AudioProcessor
from airoleplay.call_analysis.call_analyzer import CallAnalyzer

# Load environment variables
load_dotenv()

# Page config
st.set_page_config(
    page_title="AI Roleplay + Call Coaching",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        padding: 1rem 0;
    }
    .persona-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .score-card {
        background-color: #e8f4f8;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'agent' not in st.session_state:
    st.session_state.agent = None
if 'conversation_history' not in st.session_state:
    st.session_state.conversation_history = []
if 'session_started' not in st.session_state:
    st.session_state.session_started = False


def load_personas():
    """Load available personas."""
    personas_dir = Path(__file__).parent / "airoleplay" / "personas"
    return {
        "Investor – Cash Flow Focused": str(personas_dir / "investor.json"),
        "First Time Buyer – Anxious/Curious": str(personas_dir / "first_time_buyer.json"),
        "Seller / Downsizer – Convenience & Timing": str(personas_dir / "seller.json")
    }


def main():
    """Main application."""

    # Header
    st.markdown('<div class="main-header">🎯 AI Roleplay + Call Coaching System</div>', unsafe_allow_html=True)
    st.markdown("**Real Estate Sales Training with CFR Framework**")

    # Check API keys
    has_anthropic = bool(os.getenv("ANTHROPIC_API_KEY"))
    has_openai = bool(os.getenv("OPENAI_API_KEY"))

    if not has_anthropic and not has_openai:
        st.error("⚠️ No API keys configured! Please set ANTHROPIC_API_KEY and/or OPENAI_API_KEY in environment variables.")
        st.stop()

    # Sidebar
    with st.sidebar:
        st.header("Navigation")
        mode = st.radio(
            "Select Mode:",
            ["🎭 Live Roleplay Training", "📞 Analyze Call Recording", "📚 About"],
            label_visibility="collapsed"
        )

    # Route to appropriate page
    if mode == "🎭 Live Roleplay Training":
        if has_anthropic:
            live_roleplay_page()
        else:
            st.error("⚠️ ANTHROPIC_API_KEY required for roleplay training.")

    elif mode == "📞 Analyze Call Recording":
        if has_openai:
            call_analysis_page()
        else:
            st.error("⚠️ OPENAI_API_KEY required for call analysis.")

    elif mode == "📚 About":
        about_page()


def live_roleplay_page():
    """Live roleplay training page."""
    st.header("🎭 Live Roleplay Training")

    # Setup section
    if not st.session_state.session_started:
        st.subheader("Setup Your Training Session")

        col1, col2, col3 = st.columns(3)

        with col1:
            personas = load_personas()
            selected_persona = st.selectbox(
                "Select Persona",
                list(personas.keys())
            )

        with col2:
            difficulty = st.selectbox(
                "Difficulty Level",
                ["Beginner", "Medium", "Advanced"]
            )

        with col3:
            training_mode = st.selectbox(
                "Training Mode",
                ["Practice", "Scoring", "Challenge"]
            )

        # Show persona info
        if selected_persona:
            persona_path = personas[selected_persona]
            persona = PersonaCharacter.from_json(persona_path)

            with st.expander("📋 Persona Details", expanded=True):
                st.markdown(f"**Traits:** {', '.join(persona.persona_traits)}")
                st.markdown(f"**Goals:** {', '.join(persona.goals[:3])}")
                st.markdown(f"**Objections:** {len(persona.objection_patterns)} patterns")

        # Start button
        if st.button("🚀 Start Training Session", type="primary"):
            persona = PersonaCharacter.from_json(personas[selected_persona])
            agent = EnhancedRoleplayAgent(
                persona=persona,
                difficulty=difficulty.lower(),
                training_mode=training_mode.lower()
            )

            # Initialize session
            st.session_state.agent = agent
            st.session_state.persona_name = selected_persona
            st.session_state.session_started = True
            st.session_state.conversation_history = []

            # Get initial message
            initial = agent.chat(
                "Hi, I'm a real estate agent. How can I help you today?",
                thread_id="streamlit_session"
            )

            st.session_state.conversation_history.append({
                "role": "client",
                "content": initial["client_response"],
                "cooperation": initial.get("persona_cooperation", 5)
            })

            st.rerun()

    # Conversation section
    else:
        agent = st.session_state.agent
        persona_name = st.session_state.persona_name

        # Header with controls
        col1, col2 = st.columns([3, 1])
        with col1:
            st.subheader(f"💬 Conversation with {persona_name}")
        with col2:
            if st.button("🔄 End Session"):
                st.session_state.session_started = False
                st.session_state.show_summary = True
                st.rerun()

        # Display conversation
        chat_container = st.container()
        with chat_container:
            for msg in st.session_state.conversation_history:
                if msg["role"] == "client":
                    with st.chat_message("assistant", avatar="🧑"):
                        st.write(msg["content"])
                        if "cooperation" in msg:
                            st.caption(f"Cooperation: {msg['cooperation']}/10")
                else:
                    with st.chat_message("user", avatar="👤"):
                        st.write(msg["content"])
                        if "score" in msg:
                            st.caption(f"Score: {msg['score']}/{msg['max_score']}")
                            if msg.get("feedback"):
                                with st.expander("View Feedback"):
                                    for fb in msg["feedback"]:
                                        st.write(f"• {fb}")

        # Input
        user_input = st.chat_input("Type your response as a real estate agent...")

        if user_input:
            # Add user message to history
            st.session_state.conversation_history.append({
                "role": "agent",
                "content": user_input
            })

            # Get agent response
            response = agent.chat(user_input, thread_id="streamlit_session")

            # Update last agent message with scores
            if "score" in response:
                st.session_state.conversation_history[-1]["score"] = response["score"]
                st.session_state.conversation_history[-1]["max_score"] = response["max_score"]
                st.session_state.conversation_history[-1]["feedback"] = response.get("feedback", [])

            # Add client response
            st.session_state.conversation_history.append({
                "role": "client",
                "content": response["client_response"],
                "cooperation": response.get("persona_cooperation", 5)
            })

            st.rerun()

    # Show summary if session ended
    if st.session_state.get('show_summary', False):
        st.subheader("📊 Session Summary")

        if st.session_state.agent:
            summary = st.session_state.agent.get_session_summary()

            if "message" not in summary:
                # Display metrics
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Overall Score", f"{summary['total_score']}/{summary['max_score']}")
                with col2:
                    st.metric("Percentage", f"{summary['percentage']:.1f}%")
                with col3:
                    st.metric("Grade", summary['grade'])
                with col4:
                    st.metric("Cooperation", f"{summary['final_cooperation']}/10")

                # Detailed scores
                st.subheader("Detailed Scores")
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Acknowledge/Affirm", f"{summary['averages']['acknowledge_affirm']}/3")
                with col2:
                    st.metric("Isolate", f"{summary['averages']['isolate']}/3")
                with col3:
                    st.metric("Handle", f"{summary['averages']['handle']}/3")
                with col4:
                    st.metric("Close", f"{summary['averages']['close']}/2")

                # Strengths and improvements
                if summary['strengths']:
                    st.success("**✓ Strengths:**\n" + "\n".join(f"• {s}" for s in summary['strengths']))

                if summary['improvements']:
                    st.warning("**⚠️ Areas for Improvement:**\n" + "\n".join(f"• {i}" for i in summary['improvements']))

        if st.button("Start New Session"):
            st.session_state.show_summary = False
            st.session_state.session_started = False
            st.session_state.agent = None
            st.rerun()


def call_analysis_page():
    """Call recording analysis page."""
    st.header("📞 Analyze Call Recording")

    st.markdown("""
    Upload a sales call recording to get detailed CFR-based coaching feedback.
    Supports MP3, WAV, M4A formats.
    """)

    uploaded_file = st.file_uploader(
        "Upload Audio File",
        type=["mp3", "wav", "m4a"],
        help="Upload a sales call recording for analysis"
    )

    if uploaded_file is not None:
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(uploaded_file.name).suffix) as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            tmp_path = tmp_file.name

        st.success(f"✓ File uploaded: {uploaded_file.name}")

        if st.button("🔍 Analyze Call", type="primary"):
            with st.spinner("Processing call... This may take a minute."):
                try:
                    # Process audio
                    processor = AudioProcessor()
                    transcript = processor.process_call_file(tmp_path)

                    st.success(f"✓ Transcribed {len(transcript.segments)} segments")

                    # Analyze
                    analyzer = CallAnalyzer()
                    report = analyzer.analyze_call(transcript)

                    # Display results
                    st.subheader("📊 Analysis Results")

                    # Overall metrics
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Overall Score", f"{report.overall_score}/{report.max_score}")
                    with col2:
                        st.metric("Percentage", f"{report.percentage:.1f}%")
                    with col3:
                        st.metric("Grade", report.grade)

                    # Key wins
                    if report.key_wins:
                        st.success("**✓ Key Wins:**\n" + "\n".join(f"• {w}" for w in report.key_wins))

                    # Improvements
                    if report.improvement_areas:
                        st.warning("**⚠️ Areas for Improvement:**\n" + "\n".join(f"• {a}" for a in report.improvement_areas))

                    # Technique recommendations
                    if report.technique_recommendations:
                        st.info("**💡 Technique Recommendations:**\n" + "\n".join(f"• {r}" for r in report.technique_recommendations))

                    # Missed opportunities
                    if report.missed_opportunities:
                        st.subheader("🎯 Missed Opportunities")
                        for opp in report.missed_opportunities:
                            with st.expander(f"[{opp['timestamp']}] {opp['context'][:50]}..."):
                                st.write(f"**Context:** {opp['context']}")
                                st.write(f"**Suggestion:** {opp['suggestion']}")
                                if 'example' in opp:
                                    st.code(opp['example'], language=None)

                    # Download report
                    report_text = str(report)
                    st.download_button(
                        "📥 Download Full Report",
                        report_text,
                        file_name=f"{Path(uploaded_file.name).stem}_report.txt",
                        mime="text/plain"
                    )

                except Exception as e:
                    st.error(f"⚠️ Error processing call: {e}")
                    import traceback
                    st.code(traceback.format_exc())

                finally:
                    # Clean up temp file
                    try:
                        os.unlink(tmp_path)
                    except:
                        pass


def about_page():
    """About page with documentation."""
    st.header("📚 About This System")

    st.markdown("""
    ## AI Roleplay + Call Coaching System

    A comprehensive real estate sales training platform powered by deepagents and the CFR (Communicating For Real) framework.

    ### Features

    #### 🎭 Live Roleplay Training
    - **3 Realistic Personas**: Investor, First-Time Buyer, Seller/Downsizer
    - **Intelligent AI**: Responds based on your technique quality
    - **CFR Framework**: 20+ proven sales techniques
    - **Multiple Modes**: Practice, Scoring, Challenge

    #### 📞 Call Analysis
    - **Upload Real Calls**: Analyze actual conversations
    - **Automatic Transcription**: OpenAI Whisper
    - **CFR-Based Scoring**: Same framework as live training
    - **Detailed Reports**: Timestamp-specific feedback

    ### CFR Framework (4 Steps)

    1. **Acknowledge & Affirm** (0-3 points)
       - Start with: "Perfect!", "I can appreciate that"
       - Show you're listening

    2. **Isolate** (0-3 points)
       - "Besides that, is there any other reason you wouldn't...?"
       - Find all objections

    3. **Handle** (0-3 points)
       - Use techniques: Feel-Felt-Found, Has There Ever Been
       - Offer different perspective

    4. **Close** (0-2 points)
       - "Does that make sense?"
       - "Which works better for you?"

    ### Advanced Techniques

    - **Feel-Felt-Found**: "I know how you feel... clients felt the same... but found..."
    - **Has There Ever Been**: Leverage past mistakes
    - **Level Shift**: Reframe conversations
    - **Military Pattern**: 6-step persuasion
    - **Conditional Binds**: If-then logic
    - **ARP**: Acknowledge, Respond, Pivot

    ### Magic Phrases

    - "I'm not sure if it's for you, BUT..."
    - "Do you consider yourself open-minded..."
    - "How would it feel if..."
    - "Just imagine..."
    - "You have 3 options..."
    - "Two types of people..."

    ### Tips for Success

    1. **Use 4-Step Framework** in every response
    2. **Always acknowledge first** - builds rapport
    3. **Isolate objections** - find all concerns
    4. **Close every turn** - move conversation forward
    5. **Watch cooperation level** - good techniques increase it

    ### Credits

    - **CFR Framework**: Based on "Communicating For Real"
    - **Magic Phrases**: Inspired by "Exactly What to Say"
    - **Deepagents**: Built on LangChain's deepagents
    - **Transcription**: OpenAI Whisper
    """)


if __name__ == "__main__":
    main()
