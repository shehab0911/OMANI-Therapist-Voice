import React, { useState, useRef } from "react";
import { startStreamingRecording, stopRecording } from "./audioUtils";
import "./App.css";

interface Message {
  user: string;
  text: string;
}

function App() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [recording, setRecording] = useState(false);
  const [consent, setConsent] = useState(false);
  const [showDisclosure, setShowDisclosure] = useState(true);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const [partialTranscript, setPartialTranscript] = useState("");

  const handleStart = async () => {
    setRecording(true);
    wsRef.current = new WebSocket(
      (window.location.protocol === "https:" ? "wss://" : "ws://") + window.location.host + "/ws/audio"
    );
    wsRef.current.binaryType = "arraybuffer";
    wsRef.current.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.partial_transcript) setPartialTranscript(data.partial_transcript);
      if (data.final_transcript && data.response) {
        setMessages((msgs) => [
          ...msgs,
          { user: "You", text: data.final_transcript },
          { user: "Bot", text: data.response },
        ]);
        setPartialTranscript("");
        if (data.tts_audio_url) playAudio(data.tts_audio_url);
      }
    };
    mediaRecorderRef.current = await startStreamingRecording(
      (chunk: Blob) => {
        if (wsRef.current && wsRef.current.readyState === 1) {
          chunk.arrayBuffer().then((buf) => wsRef.current!.send(buf));
        }
      },
      () => {
        // Don't send end signal here - it will be sent in handleStop
        console.log("Recording stopped");
      }
    );
  };

  const handleStop = () => {
    setRecording(false);
    if (mediaRecorderRef.current) {
      stopRecording(mediaRecorderRef.current);
    }
    // Send end signal to the WebSocket and wait for response
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      try {
        // Send a JSON message to signal the end of the audio stream
        wsRef.current.send(JSON.stringify({ event: "end" }));
        // Don't close immediately - let the backend close after processing
        // The WebSocket will be closed by the backend after sending the response
      } catch (error) {
        console.error("Error sending end signal:", error);
        if (wsRef.current) wsRef.current.close();
      }
    }
  };

  const playAudio = (url: string) => {
    console.log("Attempting to play audio:", url);
    const audio = new Audio(url);
    
    audio.onloadstart = () => console.log("Audio loading started");
    audio.oncanplay = () => console.log("Audio can start playing");
    audio.onplay = () => console.log("Audio started playing");
    audio.onerror = (e) => console.error("Audio error:", e);
    audio.onended = () => console.log("Audio finished playing");
    
    audio.play().catch(error => {
      console.error("Audio play failed:", error);
    });
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
      <div className="chat-history dual-chat">
        <div className="user-column">
          <h2>You</h2>
          {messages.filter(msg => msg.user === "You").map((msg, i) => (
            <div key={i} className="user-msg">
              {msg.text}
            </div>
          ))}
          {recording && partialTranscript && (
            <div className="partial-msg" aria-live="polite">
              <b>You (speaking):</b> {partialTranscript}
            </div>
          )}
        </div>
        <div className="bot-column">
          <h2>Bot</h2>
          {messages.filter(msg => msg.user === "Bot").map((msg, i) => (
            <div key={i} className="bot-msg">
              {msg.text}
            </div>
          ))}
        </div>
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
