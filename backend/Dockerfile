# Backend Dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt ./
RUN apt-get update && apt-get install -y ffmpeg && pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]