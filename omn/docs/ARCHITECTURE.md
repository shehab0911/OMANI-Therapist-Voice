# System Architecture: OMANI Therapist Voice Chatbot

## Overview

This system is a real-time, voice-only, Omani Arabic mental health chatbot. It is designed for production use, with a focus on cultural, clinical, and security requirements.

## Components

- **Frontend (React):**
  - Real-time audio capture (WebRTC)
  - Chat UI and consent dialogs
  - Audio streaming to backend
- **Backend (FastAPI):**
  - Audio endpoint for STT
  - Intent/emotion analysis
  - Dual-model orchestration (GPT-4o + Claude Opus 4)
  - Safety and escalation logic
  - TTS synthesis
  - Session logging and security
- **Cloud Services:**
  - Google/Azure STT & TTS (Omani Arabic)
  - OpenAI GPT-4o, Anthropic Claude Opus 4
  - Secure storage (PostgreSQL, encrypted)

## Data Flow

1. User speaks (browser mic)
2. Audio sent to backend
3. STT (Omani Arabic)
4. Intent/emotion analysis
5. Safety check (crisis, escalation)
6. Dual-model response (GPT-4o primary, Claude Opus 4 fallback)
7. TTS (Omani Arabic)
8. Audio response sent to frontend

## Security & Compliance

- JWT authentication
- HTTPS enforced
- All data encrypted at rest and in transit
- Session consent and logging
- HIPAA-compliant storage

## Extensibility

- Add mobile app (React Native)
- Integrate with local clinical networks
- Expand dialect and cultural modules

See `SAFETY.md` for clinical and escalation protocols.
