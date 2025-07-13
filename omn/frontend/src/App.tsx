import React, { useState, useRef } from "react";
import { startRecording, stopRecording } from "./audioUtils.ts";
import "./App.css";

function App() {
  const [messages, setMessages] = useState([]);
  const [recording, setRecording] = useState(false);
  const [consent, setConsent] = useState(false);
  const [showDisclosure, setShowDisclosure] = useState(true);
  const mediaRecorderRef = useRef<any>(null);

  const handleStart = async () => {
    setRecording(true);
    mediaRecorderRef.current = await startRecording((audioBlob: Blob) => {
      sendAudio(audioBlob);
    });
  };

  const handleStop = () => {
    setRecording(false);
    stopRecording(mediaRecorderRef.current);
  };

  const sendAudio = async (audioBlob: Blob) => {
    const formData = new FormData();
    formData.append("audio", audioBlob, "audio.wav");
    const res = await fetch("/api/voice", { method: "POST", body: formData });
    const data = await res.json();
    setMessages((msgs) => [
      ...msgs,
      { user: "You", text: data.transcript },
      { user: "Bot", text: data.response },
    ]);
    if (data.tts_audio_url) playAudio(data.tts_audio_url);
  };

  const playAudio = (url: string) => {
    const audio = new Audio(url);
    audio.play();
  };

  if (showDisclosure) {
    return (
      <div className="app">
        <h1>OMANI Therapist Voice Chatbot</h1>
        <div className="disclosure">
          <h2>تنويه وخصوصية</h2>
          <ul>
            <li>
              هذا النظام يعتمد على الذكاء الاصطناعي، وليس بديلاً عن الاستشارة
              الطبية أو النفسية المباشرة.
            </li>
            <li>
              جميع المحادثات مسجلة ومجهولة الهوية لأغراض تحسين الخدمة وضمان
              السلامة.
            </li>
            <li>قد يتم تصعيد الحالات الحرجة إلى مختصين أو جهات طوارئ.</li>
            <li>يرجى الموافقة على الشروط للمتابعة.</li>
          </ul>
          <button
            onClick={() => {
              setConsent(true);
              setShowDisclosure(false);
            }}
          >
            أوافق وأبدأ
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="app">
      <h1>OMANI Therapist Voice Chatbot</h1>
      <div className="chat-history">
        {messages.map((msg, i) => (
          <div key={i} className={msg.user === "You" ? "user-msg" : "bot-msg"}>
            <b>{msg.user}:</b> {msg.text}
          </div>
        ))}
      </div>
      <button
        onClick={recording ? handleStop : handleStart}
        disabled={!consent}
      >
        {recording ? "Stop Recording" : "Start Talking"}
      </button>
    </div>
  );
}

export default App;
