import logging
logging.basicConfig(level=logging.INFO)
from fastapi import FastAPI, WebSocket, WebSocketDisconnect

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    logging.info("WebSocket connection attempt received")
    await websocket.accept()
    logging.info("WebSocket connection accepted")
    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_text(f"Message text was: {data}")
    except WebSocketDisconnect:
        logging.info("WebSocket disconnected")