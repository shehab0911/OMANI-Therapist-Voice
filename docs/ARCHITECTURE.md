# System Architecture: OMANI Therapist Voice Chatbot

## Overview

This system is a real-time, voice-only, Omani Arabic mental health chatbot. It is designed for production use, with a focus on cultural, clinical, and security requirements.

## Components

- **Frontend (React):**
  - Real-time audio capture (WebRTC)
  - Chat UI and consent dialogs
  - Audio streaming to backend
- **Backend (FastAPI):**
  - Audio endpoint for STT (Azure Speech-to-Text)
  - Intent/emotion analysis (OpenAI GPT-4o)
  - Dual-model orchestration (GPT-4o + Claude Opus 4)
  - Safety and escalation logic (crisis detection, referral, CBT, trauma-informed)
  - TTS synthesis (Azure Text-to-Speech)
  - Session logging and security (HIPAA-compliant)
- **Cloud Services:**
  - Azure Cognitive Services (STT/TTS)
  - OpenAI (GPT-4o)
  - Anthropic (Claude Opus 4)

## Data Flow

1. User speaks (browser mic)
2. Audio sent to backend
3. STT (Azure, Omani Arabic)
4. Intent/emotion analysis (GPT-4o)
5. Safety check (crisis, escalation, CBT, trauma-informed)
6. Dual-model response (GPT-4o primary, Claude Opus 4 fallback/validation)
7. TTS (Azure, Omani Arabic)
8. Audio response sent to frontend

## Extensibility

- Add mobile app (React Native)
- Integrate with local clinical networks
- Expand dialect and cultural modules

See `SAFETY.md` for clinical and escalation protocols.
