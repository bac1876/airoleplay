# Deployment Guide

## Deploy to Railway

Railway is the recommended platform for deploying this application.

### Prerequisites

1. **API Keys** (at minimum one of these):
   - Anthropic API key (for live roleplay training)
   - OpenAI API key (for call analysis)

2. **Railway Account**: Sign up at [railway.app](https://railway.app)

### Deployment Steps

#### Option 1: Deploy from GitHub (Recommended)

1. **Go to Railway Dashboard**
   - Visit [railway.app](https://railway.app)
   - Click "New Project"

2. **Deploy from GitHub**
   - Select "Deploy from GitHub repo"
   - Choose `airoleplay` repository
   - Railway will auto-detect the Python app

3. **Configure Environment Variables**
   - In Railway project settings, go to "Variables"
   - Add the following:

   ```
   ANTHROPIC_API_KEY=your_anthropic_key_here
   OPENAI_API_KEY=your_openai_key_here
   ```

   Optional (for LangSmith tracing):
   ```
   LANGCHAIN_API_KEY=your_langsmith_key_here
   LANGCHAIN_TRACING_V2=true
   LANGCHAIN_PROJECT=airoleplay
   ```

4. **Deploy**
   - Railway will automatically:
     - Install dependencies from `requirements.txt`
     - Use `Procfile` to start Streamlit
     - Assign a public URL

5. **Access Your App**
   - Railway will provide a URL like: `https://airoleplay-production.up.railway.app`
   - App will be live in 2-3 minutes

#### Option 2: Deploy with Railway CLI

1. **Install Railway CLI**:
   ```bash
   npm install -g @railway/cli
   ```

2. **Login**:
   ```bash
   railway login
   ```

3. **Initialize Project**:
   ```bash
   railway init
   ```

4. **Add Environment Variables**:
   ```bash
   railway variables set ANTHROPIC_API_KEY=your_key_here
   railway variables set OPENAI_API_KEY=your_key_here
   ```

5. **Deploy**:
   ```bash
   railway up
   ```

6. **Open App**:
   ```bash
   railway open
   ```

### Configuration Files

The following files are configured for Railway deployment:

- **`Procfile`**: Defines how to start the Streamlit app
  ```
  web: streamlit run app.py --server.port=$PORT --server.address=0.0.0.0
  ```

- **`requirements.txt`**: Lists all Python dependencies

- **`runtime.txt`**: Specifies Python version (3.11.9)

- **`.streamlit/config.toml`**: Streamlit configuration for production

### Environment Variables Required

| Variable | Required For | Get It From |
|----------|-------------|-------------|
| `ANTHROPIC_API_KEY` | Live roleplay training | [console.anthropic.com](https://console.anthropic.com) |
| `OPENAI_API_KEY` | Call recording analysis | [platform.openai.com](https://platform.openai.com/api-keys) |
| `LANGCHAIN_API_KEY` | Optional tracing | [smith.langchain.com](https://smith.langchain.com) |

### Post-Deployment

1. **Test the App**:
   - Visit your Railway URL
   - Try both Live Roleplay and Call Analysis features
   - Ensure API keys are working

2. **Monitor Logs**:
   ```bash
   railway logs
   ```

3. **Update App**:
   - Push to GitHub `main` branch
   - Railway auto-deploys on every push

### Troubleshooting

#### App Won't Start
- Check Railway logs: `railway logs`
- Verify environment variables are set
- Ensure API keys are valid

#### "API Key Not Found" Error
- Double-check environment variable names (case-sensitive)
- Restart Railway service after adding variables

#### Slow Transcription
- Normal for call analysis (Whisper takes 30-60 seconds)
- Consider upgrading Railway plan for better performance

#### Out of Memory
- Large audio files may cause OOM
- Upgrade Railway plan or split large files

### Cost Estimates

**Railway**:
- Hobby Plan: $5/month (sufficient for testing)
- Pro Plan: $20/month (recommended for production)

**API Costs**:
- Anthropic Claude: ~$3 per 1M input tokens
- OpenAI Whisper: $0.006 per minute of audio

### Alternative Deployment Options

#### Streamlit Cloud
- Free tier available
- Visit [streamlit.io/cloud](https://streamlit.io/cloud)
- Connect GitHub repo
- Add secrets (API keys) in Streamlit dashboard

#### Render
- Free tier with limitations
- Visit [render.com](https://render.com)
- Create new Web Service from GitHub
- Use Procfile for deployment

#### Local Deployment

Run locally with Docker:

```bash
# Build
docker build -t airoleplay .

# Run
docker run -p 8501:8501 \
  -e ANTHROPIC_API_KEY=your_key \
  -e OPENAI_API_KEY=your_key \
  airoleplay
```

(Note: Dockerfile not included, create one if needed)

### Support

For deployment issues:
- Check Railway docs: [docs.railway.app](https://docs.railway.app)
- View project README: [github.com/bac1876/airoleplay](https://github.com/bac1876/airoleplay)
