import openai
import anthropic
from google.cloud import speech_v1p1beta1 as speech
import os

async def stt_omani(audio_path):
    """
    Uses Google Cloud Speech-to-Text to transcribe Omani Arabic audio.
    Assumes audio_path is a WAV file (16kHz, mono recommended).
    """
    client = speech.SpeechClient()
    with open(audio_path, "rb") as audio_file:
        content = audio_file.read()
    audio = speech.RecognitionAudio(content=content)
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=16000,
        language_code="ar-OM",  # Omani Arabic
        enable_automatic_punctuation=True,
        model="default"
    )
    response = client.recognize(config=config, audio=audio)
    transcript = " ".join([result.alternatives[0].transcript for result in response.results])
    return transcript.strip()

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
    completion = openai.ChatCompletion.create(
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
    response = completion["choices"][0]["message"]["content"]
    # Extract JSON from response
    match = re.search(r'\{.*\}', response, re.DOTALL)
    if match:
        data = json.loads(match.group(0))
        return data.get("intent", "unknown"), data.get("emotion", "unknown")
    return "unknown", "unknown"

async def safety_check(text, intent, emotion):
    """
    Advanced safety check for crisis, self-harm, violence, and escalation triggers.
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
    # Escalate if crisis or violence detected
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
    # Escalate if emotion is severe negative
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
    Calls GPT-4o as primary, Claude Opus 4 as fallback/validator, with advanced cultural/clinical prompt.
    Returns the validated or best response.
    """
    # 1. Primary: GPT-4o with advanced prompt
    gpt_response = openai.ChatCompletion.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": _cultural_clinical_prompt(text, intent, emotion)},
            {"role": "user", "content": text}
        ],
        temperature=0.7,
    )["choices"][0]["message"]["content"]

    # 2. Fallback/Validation: Claude Opus 4 with same context
    anthropic_client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    prompt = (
        _cultural_clinical_prompt(text, intent, emotion) +
        f"\nرد GPT-4o: {gpt_response}\n"
        "قيم الرد من حيث الدقة العلاجية والثقافية، وصححه إذا لزم الأمر. أجب بالرد النهائي المناسب للمستخدم."
    )
    opus_response = anthropic_client.messages.create(
        model="claude-3-opus-20240229",
        max_tokens=512,
        messages=[{"role": "user", "content": prompt}]
    ).content[0].text

    # Prefer Claude if it makes a significant correction, else use GPT-4o
    if len(opus_response.strip()) > 0 and opus_response.strip() != gpt_response.strip():
        return opus_response.strip()
    return gpt_response.strip()

from google.cloud import texttospeech
import tempfile

async def tts_omani(text):
    """
    Uses Google Cloud Text-to-Speech to synthesize Omani Arabic audio.
    Returns the path to the generated audio file (WAV).
    """
    client = texttospeech.TextToSpeechClient()
    synthesis_input = texttospeech.SynthesisInput(text=text)
    # Use a supported Omani Arabic or closest Arabic voice
    voice = texttospeech.VoiceSelectionParams(
        language_code="ar-OM",  # Omani Arabic
        ssml_gender=texttospeech.SsmlVoiceGender.FEMALE
    )
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.LINEAR16
    )
    response = client.synthesize_speech(
        input=synthesis_input,
        voice=voice,
        audio_config=audio_config
    )
    # Save to a temp file and return the path
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav", dir="tmp") as out:
        out.write(response.audio_content)
        return out.name
