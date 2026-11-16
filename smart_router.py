"""OMID AI — Smart Router for LLM API calls (Groq)"""
import os
import json
import httpx
import asyncio
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Load .env file explicitly
from dotenv import load_dotenv
load_dotenv(dotenv_path="/sdcard/omid-ai/.env", override=True)

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

# Debug print to terminal
if GROQ_API_KEY:
    print(f"DEBUG: GROQ_API_KEY loaded: {GROQ_API_KEY[:5]}...{GROQ_API_KEY[-5:]}")
else:
    print("DEBUG: GROQ_API_KEY is EMPTY or not found in .env")

if not GROQ_API_KEY:
    raise RuntimeError("GROQ_API_KEY not set in /sdcard/omid-ai/.env")

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"


app = FastAPI(title="OMID AI Router")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    model: str
    messages: list
    temperature: float = 0.7
    max_tokens: int = 2000
    response_format: dict = None


async def call_groq_api(request: ChatRequest):
    """Call Groq API with retry logic"""
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": request.model,
        "messages": request.messages,
        "temperature": request.temperature,
        "max_tokens": request.max_tokens
    }
    
    if request.response_format:
        payload["response_format"] = request.response_format

    async with httpx.AsyncClient(timeout=120.0) as client:
        for attempt in range(3):
            try:
                response = await client.post(GROQ_API_URL, json=payload, headers=headers)
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 429:
                    await asyncio.sleep(2 ** attempt)
                    continue
                else:
                    response.raise_for_status()
            except Exception as e:
                if attempt == 2:
                    raise HTTPException(status_code=500, detail=f"API call failed: {str(e)}")
                await asyncio.sleep(2 ** attempt)


@app.post("/v1/chat/completions")
async def chat_completions(request: ChatRequest):
    """Main chat completions endpoint"""
    try:
        result = await call_groq_api(request)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check():
    return {"status": "healthy", "router": "OMID AI Smart Router"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=5001, log_level="info")
