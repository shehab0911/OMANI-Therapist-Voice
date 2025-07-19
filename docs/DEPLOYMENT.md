# Deployment Instructions

## Prerequisites

- Python 3.10+
- Node.js 18+
- Docker (for production)
- API keys for OpenAI, Anthropic, Azure STT/TTS

## Backend

1. Install dependencies:
   ```sh
   pip install -r requirements.txt
   ```
2. Run server (dev):
   ```sh
   uvicorn main:app --reload
   ```
3. For production, use Docker and HTTPS.

## Frontend

1. Install dependencies:
   ```sh
   npm install
   ```
2. Start app (dev):
   ```sh
   npm start
   ```
3. For production, build and serve static files.

## Environment Variables

- Set API keys as environment variables for backend:
  - AZURE_SPEECH_KEY
  - AZURE_SERVICE_REGION
  - OPENAI_API_KEY
  - ANTHROPIC_API_KEY
- Configure CORS and HTTPS for security

## Maintenance

- Monitor logs for crisis/escalation events
- Regularly update clinical and cultural modules

---

See `ARCHITECTURE.md` for system design and `SAFETY.md` for protocols.
