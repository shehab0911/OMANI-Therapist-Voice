import logging
logging.basicConfig(level=logging.INFO)
from fastapi import FastAPI, UploadFile, File, HTTPException, Depends, Request
from fastapi.responses import JSONResponse
import aiofiles
import uuid
import logging
import os
import subprocess
from services import stt_omani, analyze_intent_and_safety, dual_model_response, tts_omani, safety_check
from sqlalchemy.ext.asyncio import AsyncSession
from database import SessionLocal
from crud import log_conversation
from fastapi import WebSocket, WebSocketDisconnect
import tempfile
import json

app = FastAPI()

# Add CORS middleware
from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
        # Save uploaded audio file
        audio_id = str(uuid.uuid4())
        ext = os.path.splitext(audio.filename)[1].lower()
        raw_path = f"tmp/{audio_id}{ext}"
        async with aiofiles.open(raw_path, 'wb') as out_file:
            content = await audio.read()
            await out_file.write(content)
        # Always convert to wav using ffmpeg (force PCM 16kHz mono)
        audio_path = f"tmp/{audio_id}.wav"
        ffmpeg_cmd = [
            'ffmpeg', '-y', '-i', raw_path, '-ar', '16000', '-ac', '1', '-f', 'wav', audio_path
        ]
        ffmpeg_log_path = f"tmp/{audio_id}_ffmpeg.log"
        with open(ffmpeg_log_path, 'w') as ffmpeg_log:
            proc = subprocess.run(ffmpeg_cmd, stdout=ffmpeg_log, stderr=ffmpeg_log)
        if proc.returncode != 0:
            logging.error(f"ffmpeg conversion failed, see {ffmpeg_log_path}")
            raise HTTPException(status_code=500, detail="Audio conversion failed.")
        else:
            audio_path = raw_path
    except Exception as e:
        logging.exception("Failed to save or convert audio file.")
        raise HTTPException(status_code=500, detail="Failed to save or convert audio file.")

    try:
        # 1. Speech-to-Text (Omani Arabic)
        transcript = await stt_omani(audio_path)
    except Exception as e:
        logging.exception("Speech-to-text failed.")
        raise HTTPException(status_code=500, detail="Speech-to-text failed.")

    try:
        # 2. Intent & Emotion Analysis + Safety Check (parallelized)
        intent, emotion, safety_result = await analyze_intent_and_safety(transcript)
        escalate = safety_result["escalate"]
        if escalate:
            # Log conversation with escalation
            await log_conversation(db, audio_id, transcript, safety_result["message"], intent, emotion, True)
            return JSONResponse({"response": safety_result["message"], "transcript": transcript, "tts_audio_url": ""})
    except Exception as e:
        logging.exception("Intent/emotion analysis or safety check failed.")
        raise HTTPException(status_code=500, detail="Intent/emotion analysis or safety check failed.")

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
        # 4. Generate bot response using dual-model fallback (GPT-4o primary, Claude Opus 4 fallback)
        response_text = await dual_model_response(transcript, intent, emotion)
    except Exception as e:
        logging.exception("Response generation failed.")
        raise HTTPException(status_code=500, detail="Response generation failed.")

    try:
        # 5. Synthesize TTS (Omani Arabic)
        tts_audio_url = await tts_omani(response_text)
    except Exception as e:
        logging.exception("Text-to-speech failed.")
        raise HTTPException(status_code=500, detail="Text-to-speech failed.")

    # Log conversation (no escalation)
    await log_conversation(db, audio_id, transcript, response_text, intent, emotion, False)
    return {"transcript": transcript, "response": response_text, "tts_audio_url": tts_audio_url}


@app.get("/test")
async def test_endpoint():
    return {"message": "Test endpoint"}

@app.get("/api/audio/{filename}")
async def serve_audio(filename: str):
    """Serve audio files for TTS playback"""
    from fastapi.responses import FileResponse
    import os
    
    file_path = f"tmp/{filename}"
    if os.path.exists(file_path):
        return FileResponse(file_path, media_type="audio/wav")
    else:
        raise HTTPException(status_code=404, detail="Audio file not found")


@app.websocket("/ws")
async def websocket_text_endpoint(websocket: WebSocket):
    """WebSocket endpoint for text-based conversations"""
    logging.info("Text WebSocket connection attempt received")
    logging.info(f"WebSocket headers: {websocket.headers}")
    try:
        # Accept connection without origin restrictions
        await websocket.accept()
        logging.info("Text WebSocket connection accepted")
    except Exception as e:
        logging.error(f"Failed to accept WebSocket connection: {e}")
        return
    
    try:
        while True:
            # Receive text message
            data = await websocket.receive_text()
            logging.info(f"Received text message: {data}")
            
            try:
                message_data = json.loads(data)
                user_message = message_data.get("message", "")
                
                if user_message:
                    # 1. Intent & Emotion Analysis
                    intent, emotion, safety_result = await analyze_intent_and_safety(user_message)
                    logging.info(f"Intent: {intent}, Emotion: {emotion}")
                    
                    # 2. Safety Check
                    safety_result = await safety_check(user_message, intent, emotion)
                    escalate = safety_result["escalate"]
                    
                    if escalate:
                        response_text = safety_result["message"]
                        tts_audio_url = ""
                    else:
                        # 3. Generate response
                        response_text = await dual_model_response(user_message, intent, emotion)
                        logging.info(f"Response: {response_text}")
                        
                        # 4. Text-to-Speech
                        tts_audio_url = await tts_omani(response_text)
                        logging.info(f"TTS URL: {tts_audio_url}")
                    
                    # Send response
                    await websocket.send_text(json.dumps({
                        "transcript": user_message,
                        "response": response_text,
                        "tts_audio_url": tts_audio_url
                    }))
                    
            except json.JSONDecodeError:
                logging.error(f"Invalid JSON received: {data}")
                await websocket.send_text(json.dumps({"error": "Invalid JSON format"}))
                
    except WebSocketDisconnect:
        logging.info("Text WebSocket disconnected")
    except Exception as e:
        logging.exception(f"Text WebSocket error: {e}")


@app.websocket("/ws/audio")
async def websocket_audio_endpoint(websocket: WebSocket):
    logging.info("WebSocket connection attempt received")
    await websocket.accept()
    logging.info("WebSocket connection accepted")
    
    # Create a temporary file to store audio chunks
    temp_audio = tempfile.NamedTemporaryFile(delete=False, suffix=".webm")
    audio_chunks = []
    
    try:
        while True:
            # Use receive() to handle both binary and text messages
            message = await websocket.receive()
            
            if "bytes" in message:
                # Handle binary audio data
                data = message["bytes"]
                logging.info(f"Received {len(data)} bytes")
                temp_audio.write(data)
                audio_chunks.append(data)
                # Send partial transcript update
                await websocket.send_json({"partial_transcript": "Processing your speech..."})
                
            elif "text" in message:
                # Handle text messages (like end signal)
                text_data = message["text"]
                logging.info(f"Received text: {text_data}")
                
                try:
                    json_data = json.loads(text_data)
                    if json_data.get("event") == "end":
                        logging.info("Received end signal from client")
                        # Close the temp file
                        temp_audio.close()
                        
                        # Process the complete audio file
                        audio_id = str(uuid.uuid4())
                        wav_path = f"tmp/{audio_id}.wav"
                        
                        # Convert to wav using ffmpeg
                        ffmpeg_cmd = [
                            'ffmpeg', '-y', '-i', temp_audio.name, '-ar', '16000', '-ac', '1', '-f', 'wav', wav_path
                        ]
                        proc = subprocess.run(ffmpeg_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                        
                        if proc.returncode != 0:
                            logging.error(f"ffmpeg conversion failed: {proc.stderr.decode()}")
                            await websocket.send_json({"error": "Audio conversion failed."})
                            break
                            
                        # Process the audio with STT
                        try:
                            # 1. Speech-to-Text (Omani Arabic)
                            transcript = await stt_omani(wav_path)
                            logging.info(f"Transcript: {transcript}")
                            
                            # 2. Intent & Emotion Analysis
                            intent, emotion, safety_result = await analyze_intent_and_safety(transcript)
                            logging.info(f"Intent: {intent}, Emotion: {emotion}")
                            
                            # 3. Safety Check
                            safety_result = await safety_check(transcript, intent, emotion)
                            escalate = safety_result["escalate"]
                            
                            if escalate:
                                await websocket.send_json({
                                    "final_transcript": transcript,
                                    "response": safety_result["message"],
                                    "tts_audio_url": ""
                                })
                                
                                # Close the WebSocket connection gracefully
                                await websocket.close()
                            else:
                                # 4. Generate response
                                response_text = await dual_model_response(transcript, intent, emotion)
                                logging.info(f"Response: {response_text}")
                                
                                # 5. Text-to-Speech
                                tts_audio_url = await tts_omani(response_text)
                                logging.info(f"TTS URL: {tts_audio_url}")
                                
                                # Send final response
                                await websocket.send_json({
                                    "final_transcript": transcript,
                                    "response": response_text,
                                    "tts_audio_url": tts_audio_url
                                })
                                
                                # Close the WebSocket connection gracefully
                                await websocket.close()
                                
                        except Exception as process_error:
                            logging.exception(f"Error processing audio: {process_error}")
                            await websocket.send_json({"error": "Failed to process audio."})
                        
                        # Clean up
                        try:
                            os.unlink(temp_audio.name)
                            os.unlink(wav_path)
                        except:
                            pass
                            
                        break
                        
                except json.JSONDecodeError:
                    logging.error(f"Invalid JSON received: {text_data}")
                    
    except WebSocketDisconnect:
        logging.info("WebSocket disconnected")
    except Exception as e:
        logging.exception(f"WebSocket error: {e}")
    finally:
        try:
            # Make sure temp file is closed and removed
            if 'temp_audio' in locals():
                try:
                    temp_audio.close()
                    os.unlink(temp_audio.name)
                except:
                    pass
        except Exception as cleanup_error:
            logging.error(f"Cleanup error: {cleanup_error}")
