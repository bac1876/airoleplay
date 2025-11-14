# AI Roleplay + Call Coaching System

A comprehensive real estate sales training platform powered by deepagents and the CFR (Communicating For Real) framework.

## Features

### 🎭 Live Roleplay Training
- **3 Realistic Personas**: Investor, First-Time Buyer, Seller/Downsizer
- **Intelligent AI Clients**: Respond based on your technique quality
- **CFR Framework Integration**: 20+ proven sales techniques
- **Multiple Difficulty Levels**: Beginner, Medium, Advanced
- **Training Modes**:
  - **Practice Mode**: Detailed coaching after each turn
  - **Scoring Mode**: Real-time performance feedback
  - **Challenge Mode**: Test yourself without help

### 📞 Call Recording Analysis
- **Upload Real Calls**: Analyze actual sales conversations
- **Automatic Transcription**: Uses OpenAI Whisper
- **Speaker Identification**: Separates agent from client
- **CFR-Based Scoring**: Same framework as live training
- **Detailed Coaching Reports**:
  - Timestamp-specific feedback
  - Missed opportunities
  - Technique recommendations
  - Before/After script examples

### 📊 Advanced Scoring System
- **4-Step CFR Framework**:
  1. Acknowledge & Affirm (0-3 points)
  2. Isolate Objection (0-3 points)
  3. Handle Objection (0-3 points)
  4. Close (0-2 points)
- **Magic Phrase Detection**: From "Exactly What to Say"
- **Technique Recognition**: Feel-Felt-Found, Military Pattern, Level Shift, etc.
- **Rapport Breaker Detection**: Warns when you break rapport

## Installation

### 1. Clone & Setup

```bash
cd airoleplay
pip install -e .
```

Or with uv:
```bash
uv pip install -e .
```

### 2. Configure API Keys

Copy the example env file:
```bash
cp .env.example .env
```

Edit `.env` and add your keys:
```
# Required for live roleplay
ANTHROPIC_API_KEY=your_anthropic_key_here

# Required for call analysis
OPENAI_API_KEY=your_openai_key_here

# Optional: LangSmith tracing
LANGCHAIN_API_KEY=your_langsmith_key_here
LANGCHAIN_TRACING_V2=true
LANGCHAIN_PROJECT=airoleplay
```

### 3. Run the Application

```bash
python main.py
```

## Usage

### Live Roleplay Training

1. Select **Option 1** from main menu
2. Choose a persona:
   - **Investor**: Numbers-driven, skeptical, focused on ROI
   - **First-Time Buyer**: Anxious, needs reassurance, price-sensitive
   - **Seller**: Practical, timeline-focused, convenience-oriented

3. Select difficulty level:
   - **Beginner**: 2 easy objections
   - **Medium**: 4 moderate objections
   - **Advanced**: All objections with layers

4. Choose training mode:
   - **Practice**: See coaching after each response
   - **Scoring**: See score and cooperation level
   - **Challenge**: No feedback until end

5. Practice CFR techniques:
   ```
   Client: "Cap rate seems too low on this property"

   You: "Perfect! You're absolutely right to focus on cap rate -
   that's the key metric for any investment property. Out of
   curiosity, besides the cap rate, is there anything else that
   would keep you from moving forward on this property?"

   [Score: 9/11 | Cooperation: 7/10]

   ✓ Excellent acknowledgement
   ✓ Good isolation question
   ```

6. Type `end` to finish and see summary

### Call Recording Analysis

1. Select **Option 2** from main menu
2. Provide path to audio file (MP3, WAV, M4A)
3. System will:
   - Transcribe with Whisper
   - Identify speakers (agent vs client)
   - Score each agent response
   - Generate coaching report

4. Review detailed feedback:
   ```
   [2:35] Missing isolation - Client raised objection but you didn't isolate
   → Suggested: Ask "Besides that, is there any other reason you wouldn't...?"

   [4:12] Rapport breaker: Used 'I understand' without qualifier
   → Suggested: Use 'I can appreciate that' instead
   ```

5. Save report for later review

## CFR Techniques Included

### Core Framework
- **PACE & LEAD**: Build agreement then guide
- **5 YES Technique**: Get 5 agreements then close
- **4-Step Objection Handling**: Acknowledge → Isolate → Handle → Close

### Advanced Techniques
- **Feel-Felt-Found**: Empathy through client stories
- **Has There Ever Been**: Leverage past mistakes
- **Level Shift**: Reframe conversations
- **Military Pattern**: 6-step persuasion framework
- **Conditional Binds**: If-then logic
- **ARP**: Acknowledge, Respond, Pivot

### Magic Phrases
- "I'm not sure if it's for you, BUT..."
- "Do you consider yourself open-minded..."
- "How would it feel if..."
- "I'm guessing you haven't gotten around to..."
- "Just imagine..."
- "You have 3 options..."
- "Two types of people..."
- "Before you make your mind up..."
- "5 to 7 clients"

## Project Structure

```
airoleplay/
├── airoleplay/
│   ├── agents/              # Roleplay agents
│   │   ├── roleplay_agent.py
│   │   └── enhanced_roleplay_agent.py
│   ├── characters/          # Character/Persona system
│   │   ├── base.py
│   │   └── persona_character.py
│   ├── personas/            # Persona JSON files
│   │   ├── investor.json
│   │   ├── first_time_buyer.json
│   │   └── seller.json
│   ├── data/                # Techniques and phrases
│   │   ├── techniques.json
│   │   └── magic_phrases.json
│   ├── scoring/             # CFR scoring engine
│   │   └── conversation_scorer.py
│   └── call_analysis/       # Call recording analysis
│       ├── audio_processor.py
│       └── call_analyzer.py
├── main.py                  # Main application
├── pyproject.toml
└── README.md
```

## Creating Custom Personas

Create a new JSON file in `airoleplay/personas/`:

```json
{
  "id": "custom_persona_v1",
  "label": "Your Persona Label",
  "tone": {
    "formality": "medium",
    "energy": "warm",
    "pace_wpm": 130,
    "directness": "high"
  },
  "persona_traits": ["trait1", "trait2"],
  "context": {
    "market": "Denver",
    "budget": "400-500k",
    "timeline": "60 days"
  },
  "goals": ["goal1", "goal2"],
  "objection_patterns": [
    {
      "name": "ObjectionName",
      "trigger_phrases": ["phrase1", "phrase2"],
      "emotion": "concerned",
      "response_playbook": [
        "Step 1: Acknowledge",
        "Step 2: Reframe",
        "Step 3: Offer solution"
      ],
      "evidence": ["data point 1", "data point 2"],
      "magic_phrases": ["open_minded", "three_options"]
    }
  ],
  "knowledge_snippets": ["snippet1", "snippet2"],
  "escalation_rules": {
    "handoff_if": ["complex question type"],
    "handoff_target": "Senior Specialist"
  }
}
```

## Tips for Best Results

### Live Roleplay
1. **Use the 4-Step Framework** in every response
2. **Start with acknowledgement**: "Perfect!", "I can appreciate that"
3. **Always isolate**: "Besides that, is there any other concern?"
4. **Close every turn**: "Does that make sense?"
5. **Watch cooperation level**: Good techniques = higher cooperation

### Call Analysis
1. **Use clear audio files**: Better transcription = better analysis
2. **Real conversations work best**: Actual calls provide best feedback
3. **Review timestamped feedback**: Focus on missed opportunities
4. **Practice suggested techniques**: Apply to next call

## Common Issues

### "ANTHROPIC_API_KEY not found"
- Create `.env` file with your API key
- Get key from: https://console.anthropic.com/

### "OPENAI_API_KEY not found" (call analysis only)
- Add OpenAI key to `.env` file
- Get key from: https://platform.openai.com/api-keys

### Audio file not transcribing
- Ensure file is MP3, WAV, or M4A format
- Check file size (recommended < 25MB)
- Verify audio quality

## Credits

- **CFR Framework**: Based on "Communicating For Real" sales training
- **Magic Phrases**: Inspired by "Exactly What to Say"
- **Deepagents**: Built on [deepagents](https://github.com/langchain-ai/deepagents) by LangChain
- **Transcription**: Powered by OpenAI Whisper

## License

MIT

## Support

For issues or questions:
- Check documentation in this README
- Review persona JSON examples
- Test with beginner difficulty first
