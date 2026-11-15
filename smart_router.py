import os
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import requests
import uvicorn
import traceback

app = FastAPI()

# خواندن مستقیم و مطمئن فایل .env
GROQ_API_KEY = ""
try:
    with open("/sdcard/omid-ai/.env", "r") as f:
        for line in f:
            if line.startswith("GROQ_API_KEY="):
                # پاک کردن فاصله‌ها و کوتیشن‌های احتمالی
                GROQ_API_KEY = line.strip().split("=", 1)[1].strip().strip('"').strip("'")
                break
except Exception as e:
    print(f"Error reading .env: {e}")

if not GROQ_API_KEY:
    print("\n⚠️ WARNING: API Key is empty! Please check .env file.\n")

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

@app.post("/v1/chat/completions")
@app.post("/v1/messages")
async def route_any(request: Request):
    try:
        data = await request.json()
        messages = data.get("messages", [])
        
        if data.get("system"):
            messages.insert(0, {"role": "system", "content": data["system"]})

        headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
        payload = {"model": "openai/gpt-oss-120b", "messages": messages}

        response = requests.post(GROQ_URL, headers=headers, json=payload)
        result = response.json()

        if "error" in result:
            print(f"\n--- GROQ ERROR: {result['error']} ---\n")
            return JSONResponse({"error": result["error"]}, status_code=500)

        content = result["choices"][0]["message"]["content"]
        return JSONResponse({"choices": result.get("choices", []), "content": [{"type": "text", "text": content}]})
    except Exception as e:
        print("\n--- ERROR ---")
        print(traceback.format_exc())
        return JSONResponse({"error": str(e)}, status_code=500)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5001)
