export async function startRecording(onStop: (audioBlob: Blob) => void) {
  const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
  // Use browser-supported format (webm)
  const mediaRecorder = new MediaRecorder(stream, { mimeType: 'audio/webm' });
  const audioChunks: Blob[] = [];
  mediaRecorder.ondataavailable = (event) => audioChunks.push(event.data);
  mediaRecorder.onstop = () => {
    const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
    onStop(audioBlob);
  };
  mediaRecorder.start();
  return mediaRecorder;
}

export async function startStreamingRecording(onChunk: (chunk: Blob) => void, onStop: () => void) {
  const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
  const mediaRecorder = new MediaRecorder(stream, { mimeType: 'audio/webm' });
  mediaRecorder.ondataavailable = (event) => {
    if (event.data && event.data.size > 0) {
      onChunk(event.data);
    }
  };
  mediaRecorder.onstop = onStop;
  mediaRecorder.start(250); // Emit chunks every 250ms
  return mediaRecorder;
}

export function stopRecording(mediaRecorder: MediaRecorder) {
  if (mediaRecorder && mediaRecorder.state !== "inactive") {
    mediaRecorder.stop();
  }
}
