from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from fastapi.responses import JSONResponse
import aiofiles
import uuid
import logging
from services import stt_omani, analyze_intent, dual_model_response, tts_omani, safety_check
from sqlalchemy.ext.asyncio import AsyncSession
from database import SessionLocal
from crud import log_conversation

app = FastAPI()

# Dependency to get DB session
async def get_db():
    async with SessionLocal() as session:
        yield session

@app.post("/api/voice")
async def process_voice(
    audio: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    try:
        # Save audio file
        audio_id = str(uuid.uuid4())
        audio_path = f"tmp/{audio_id}.wav"
        async with aiofiles.open(audio_path, 'wb') as out_file:
            content = await audio.read()
            await out_file.write(content)
    except Exception as e:
        logging.exception("Failed to save audio file.")
        raise HTTPException(status_code=500, detail="Failed to save audio file.")

    try:
        # 1. Speech-to-Text (Omani Arabic)
        transcript = await stt_omani(audio_path)
    except Exception as e:
        logging.exception("Speech-to-text failed.")
        raise HTTPException(status_code=500, detail="Speech-to-text failed.")

    try:
        # 2. Intent & Emotion Analysis
        intent, emotion = await analyze_intent(transcript)
    except Exception as e:
        logging.exception("Intent/emotion analysis failed.")
        raise HTTPException(status_code=500, detail="Intent/emotion analysis failed.")

    try:
        # 3. Safety & Crisis Check
        safety_result = await safety_check(transcript, intent, emotion)
        escalate = safety_result["escalate"]
        if escalate:
            # Log conversation with escalation
            await log_conversation(db, audio_id, transcript, safety_result["message"], intent, emotion, True)
            return JSONResponse({"response": safety_result["message"], "transcript": transcript, "tts_audio_url": ""})
    except Exception as e:
        logging.exception("Safety check failed.")
        raise HTTPException(status_code=500, detail="Safety check failed.")

    try:
        # 4. Dual-Model Response Generation
        response = await dual_model_response(transcript, intent, emotion)
    except Exception as e:
        logging.exception("Response generation failed.")
        raise HTTPException(status_code=500, detail="Response generation failed.")

    try:
        # 5. TTS (Omani Arabic)
        tts_audio_url = await tts_omani(response)
    except Exception as e:
        logging.exception("Text-to-speech failed.")
        raise HTTPException(status_code=500, detail="Text-to-speech failed.")

    # Log conversation (no escalation)
    await log_conversation(db, audio_id, transcript, response, intent, emotion, False)
    return {"transcript": transcript, "response": response, "tts_audio_url": tts_audio_url}
