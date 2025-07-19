#!/usr/bin/env python3
import asyncio
import os
from services import tts_omani

async def test_tts():
    print("Testing TTS with simple Arabic text...")
    result = await tts_omani("مرحبا، كيف حالك؟")
    print(f"TTS Result: {result}")
    
    if result:
        print("TTS test successful!")
        # Check if file exists
        filename = result.split('/')[-1]
        filepath = f"tmp/{filename}"
        if os.path.exists(filepath):
            print(f"Audio file created: {filepath}")
            print(f"File size: {os.path.getsize(filepath)} bytes")
        else:
            print(f"Audio file not found: {filepath}")
    else:
        print("TTS test failed!")

if __name__ == "__main__":
    asyncio.run(test_tts())