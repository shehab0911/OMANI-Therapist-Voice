# OMANI Therapist Voice Chatbot

## Overview

A production-ready, real-time, voice-only Omani Arabic mental health chatbot. This system provides culturally sensitive, therapeutic-grade conversations with real-time speech processing and safety protocols.

## Features

- Real-time Omani Arabic voice chat (Azure STT & TTS)
- Dual-model response (GPT-4o + Claude Opus 4)
- Cultural and clinical adaptation (CBT, trauma-informed, Islamic values)
- Crisis detection and escalation (safety protocols, professional referral)
- Secure, HIPAA-compliant data handling
- Code-switching (Arabic-English mix)
- Emotional nuance and intent analysis
- Real-time streaming UI with partial transcript feedback
- Optimized backend for low latency (parallelized intent/emotion/safety, async TTS)
- Robust conversation logging for clinical review

## Project Structure

- `backend/`: FastAPI backend, Azure STT/TTS, dual-model orchestration, safety logic
- `frontend/`: React UI, real-time audio capture, consent dialogs
- `docs/`: Architecture, safety, deployment, and cultural adaptation guides

## Environment Variables

- AZURE_SPEECH_KEY
- AZURE_SERVICE_REGION
- OPENAI_API_KEY
- ANTHROPIC_API_KEY

---

See `ARCHITECTURE.md` for system design and `SAFETY.md` for protocols.
