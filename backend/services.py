import openai
import anthropic
import azure.cognitiveservices.speech as speechsdk
import os
import tempfile
import asyncio

async def stt_omani(audio_path):
    """
    Uses Azure Speech-to-Text to transcribe Omani Arabic audio.
    Assumes audio_path is a WAV file (16kHz, mono recommended).
    """
    speech_key = os.getenv("AZURE_SPEECH_KEY")
    service_region = os.getenv("AZURE_SERVICE_REGION")
    speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=service_region)
    speech_config.speech_recognition_language = "ar-OM"
    audio_input = speechsdk.AudioConfig(filename=audio_path)
    speech_recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_input)
    result = speech_recognizer.recognize_once()
    if result.reason == speechsdk.ResultReason.RecognizedSpeech:
        return result.text.strip()
    else:
        return ""

async def analyze_intent(text):
    """
    Uses OpenAI GPT-4o to analyze intent and emotion from the user's text.
    Returns (intent, emotion) as strings.
    """
    system_prompt = (
        "أنت محلل نفسي عماني محترف. استخرج نية المستخدم (استشارة، أزمة، دعم، إلخ) "
        "واستخرج الشعور الأساسي (قلق، حزن، غضب، أمل، إلخ) من النص التالي. "
        "أجب فقط بصيغة JSON: {\"intent\": intent, \"emotion\": emotion}"
    )
    client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    completion = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": text}
        ],
        temperature=0.2,
        max_tokens=100
    )
    import json
    import re
    response = completion.choices[0].message.content
    match = re.search(r'\{.*\}', response, re.DOTALL)
    if match:
        data = json.loads(match.group(0))
        return data.get("intent", "unknown"), data.get("emotion", "unknown")
    return "unknown", "unknown"

async def safety_check(text, intent, emotion):
    """
    Advanced safety check for Crisis, self-harm, violence, and escalation triggers.
    Returns escalation status and appropriate message.
    """
    crisis_keywords = [
        "انتحار", "أنتحر", "أقتل نفسي", "أموت", "أموت نفسي", "suicide", "kill myself", "die", "self-harm", "إيذاء نفسي"
    ]
    violence_keywords = [
        "قتل", "عنف", "أؤذي أحد", "أؤذي شخص", "violence", "harm someone"
    ]
    referral_keywords = [
        "طبيب نفسي", "مستشفى", "مساعدة مختص", "أحتاج مختص", "أحتاج طبيب", "أحتاج علاج", "أحتاج دعم"
    ]
    if any(k in text for k in crisis_keywords) or intent == "crisis":
        return {
            "escalate": True,
            "message": "يبدو أنك تمر بأزمة حرجة. أنصحك بالتواصل فوراً مع جهة طوارئ أو مختص نفسي. هل ترغب في الاتصال بخط المساعدة الوطني: 1234؟"
        }
    if any(k in text for k in violence_keywords):
        return {
            "escalate": True,
            "message": "تم رصد إشارات عنف. سيتم تصعيد الجلسة لمختص فوراً حفاظاً على سلامتك وسلامة الآخرين."
        }
    if any(k in text for k in referral_keywords):
        return {
            "escalate": True,
            "message": "يبدو أنك بحاجة لدعم مختص. هل ترغب في التواصل مع طبيب أو مستشفى معتمد؟"
        }
    if emotion in ["يأس", "حزن شديد", "غضب شديد", "خوف شديد"]:
        return {
            "escalate": True,
            "message": "أشعر أنك تمر بمشاعر صعبة جداً. أنصحك بالتواصل مع مختص أو جهة دعم فوراً."
        }
    return {"escalate": False}

def _cultural_clinical_prompt(text, intent, emotion):
    return (
        "أنت معالج نفسي عماني محترف. تحدث باللهجة العمانية وراعِ القيم الإسلامية. "
        "استخدم مصطلحات الصحة النفسية الخليجية، وادعم المزج بين العربية والإنجليزية إذا استخدمها المستخدم. "
        "راعِ القيم الأسرية والدينية، وادعم المستخدم بتقنيات العلاج المعرفي السلوكي (CBT) عند الحاجة. "
        "إذا كان هناك أزمة أو خطر، فعّل بروتوكول التصعيد وقدم دعمًا عاجلاً. "
        f"نية المستخدم: {intent}\nشعور المستخدم: {emotion}\nالنص: {text}"
    )

async def dual_model_response(text, intent, emotion):
    """
    Ultra-fast response generation optimized for Omani Arabic conversations.
    Uses GPT-4o-mini for instant responses with cultural adaptation.
    """
    import logging
    
    client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    # Optimized system prompt for faster processing
    system_prompt = (
        "أنت معالج نفسي عماني. تحدث باللهجة العمانية بشكل طبيعي ومريح. "
        "قدم ردود قصيرة ومفيدة (50-100 كلمة). راعِ القيم الإسلامية والثقافة العمانية. "
        f"المشاعر: {emotion}، النية: {intent}"
    )
    
    try:
        # Use GPT-4o-mini for ultra-fast responses
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": text}
            ],
            temperature=0.8,  # Slightly higher for more natural responses
            max_tokens=150,   # Reduced for faster response
            timeout=10        # 10 second timeout for instant response
        )
        
        result = response.choices[0].message.content.strip()
        logging.info(f"Generated response in Omani Arabic: {len(result)} characters")
        return result
        
    except Exception as e:
        logging.error(f"Response generation failed: {e}")
        # Fallback response in Omani Arabic
        return "أعتذر، حدث خطأ تقني. هل يمكنك إعادة المحاولة؟"

async def analyze_intent_and_safety(text):
    intent_emotion_task = asyncio.create_task(analyze_intent(text))
    # Wait for intent/emotion to finish, then run safety check
    intent, emotion = await intent_emotion_task
    safety_task = asyncio.create_task(safety_check(text, intent, emotion))
    safety_result = await safety_task
    return intent, emotion, safety_result

async def tts_omani(text):
    import logging
    import uuid
    
    speech_key = os.getenv("AZURE_SPEECH_KEY")
    service_region = os.getenv("AZURE_SERVICE_REGION")
    
    if not speech_key or not service_region:
        logging.error("Azure Speech credentials not found")
        return ""
    
    # Prioritize Omani Arabic voice for instant response
    voice_name = "ar-SA-HamedNeural"  # Use Saudi Arabic as primary (faster and more reliable)
    language = "ar-SA"
    
    try:
        speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=service_region)
        speech_config.speech_synthesis_language = language
        speech_config.speech_synthesis_voice_name = voice_name
        
        # Set output format for optimization
        speech_config.set_speech_synthesis_output_format(speechsdk.SpeechSynthesisOutputFormat.Audio16Khz32KBitRateMonoMp3)
        
        # Create synthesizer without audio config to get audio data directly
        synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=None)
        
        # Use executor for non-blocking synthesis
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, lambda: synthesizer.speak_text_async(text).get())
        
        logging.info(f"TTS attempt with {voice_name}: {result.reason}")
        
        if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
            audio_id = str(uuid.uuid4())
            filename = f"{audio_id}.wav"
            filepath = f"tmp/{filename}"
            
            # Ensure tmp directory exists
            os.makedirs("tmp", exist_ok=True)
            
            # Write audio data immediately
            with open(filepath, "wb") as out:
                out.write(result.audio_data)
            
            logging.info(f"TTS success with {voice_name}: {filepath}, size: {len(result.audio_data)} bytes")
            # Return absolute URL that frontend can access from different port
            return f"http://localhost:8000/api/audio/{filename}"
        elif result.reason == speechsdk.ResultReason.Canceled:
            cancellation_details = speechsdk.CancellationDetails(result)
            logging.error(f"TTS canceled with {voice_name}: {cancellation_details.reason}, {cancellation_details.error_details}")
        else:
            logging.error(f"TTS failed with {voice_name}: {result.reason}")
            
    except Exception as e:
        logging.error(f"TTS error with {voice_name}: {e}")
    
    # Fallback: return empty string if TTS fails
    logging.error("TTS failed - no audio will be generated")
    return ""
