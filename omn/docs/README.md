# OMANI Therapist Voice Chatbot

## Overview

A production-ready, real-time, voice-only Omani Arabic mental health chatbot. This system provides culturally sensitive, therapeutic-grade conversations with real-time speech processing and safety protocols.

## Features

- Real-time Omani Arabic voice chat (STT & TTS)
- Dual-model response (GPT-4o + Claude Opus 4)
- Cultural and clinical adaptation
- Crisis detection and escalation
- Secure, HIPAA-compliant data handling

## Project Structure

- `/frontend` — React web app for real-time voice chat
- `/backend` — FastAPI server for audio, NLP, and safety
- `/docs` — Documentation and deployment guides

## Quick Start

1. Install backend dependencies:
   ```sh
   cd backend
   pip install -r requirements.txt
   ```
2. Start backend:
   ```sh
   uvicorn main:app --reload
   ```
3. Install frontend dependencies:
   ```sh
   cd ../frontend
   npm install
   npm start
   ```

## Deployment

- Use Docker and HTTPS for production
- Integrate with Google/Azure STT/TTS for Omani Arabic
- Set up OpenAI and Anthropic API keys

## Safety & Clinical Protocols

- All conversations are checked for crisis and escalation
- Emergency contact and referral triggers included
- Data privacy and user consent enforced

## See `ARCHITECTURE.md` and `SAFETY.md` for more details.
