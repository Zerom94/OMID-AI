"""OMID AI - FastAPI Backend with SSE"""
import os
import glob
import json
import asyncio
import datetime
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from agents.base import BaseAgent
from core.manager import ManagerAgent
from core.db import get_db

app = FastAPI(title="OMID AI")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

os.makedirs("static", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

manager = ManagerAgent(config={}, memory=get_db())
sse_queues = set()

async def broadcast_event(event_type: str, data: dict):
    message = {
        "event": event_type,
        "data": data,
        "timestamp": datetime.datetime.now().isoformat()
    }
    dead_queues = set()
    for queue in sse_queues:
        try:
            queue.put_nowait(message)
        except asyncio.QueueFull:
            dead_queues.add(queue)
    sse_queues -= dead_queues

BaseAgent.log_callback = broadcast_event

class ChatRequest(BaseModel):
    message: str

@app.get("/", response_class=HTMLResponse)
async def serve_ui():
    html_path = "index.html"
    if os.path.exists(html_path):
        with open(html_path, "r", encoding="utf-8") as f:
            return HTMLResponse(f.read())
    return HTMLResponse("<h1>OMID AI - Index not found</h1>")

@app.post("/api/chat")
async def chat_endpoint(request: ChatRequest):
    try:
        results = await manager.plan_and_dispatch(request.message)
        response_text = ""
        for result in results:
            if result and result.success:
                if isinstance(result.output, str):
                    response_text += result.output + "\n"
                elif isinstance(result.output, dict):
                    if "persian_report" in result.output:
                        response_text += result.output.get("persian_report") + "\n"
                    elif "code" in result.output:
                        response_text += result.output["code"] + "\n"
                    else:
                        response_text += json.dumps(result.output, ensure_ascii=False, indent=2) + "\n"
            else:
                error_msg = result.error if result else "Unknown error"
                response_text += f"❌ Error: {error_msg}\n"
        return {"response": response_text.strip(), "success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/mission")
async def mission_endpoint(request: ChatRequest):
    return await chat_endpoint(request)

@app.get("/api/files")
async def get_files():
    """List all .py files inside the src/ directory for the Code Explorer"""
    files = []
    if os.path.exists("src"):
        for path in glob.glob("src/**/*.py", recursive=True):
            files.append(os.path.relpath(path, "src"))
    files.sort()
    return {"files": files}

@app.get("/api/projects")
async def get_projects():
    db = get_db()
    with db.get_connection() as conn:
        rows = conn.execute("SELECT * FROM projects ORDER BY created_at DESC").fetchall()
        return {"projects": [dict(row) for row in rows]}

@app.get("/api/security-scans")
async def get_security_scans():
    db = get_db()
    with db.get_connection() as conn:
        rows = conn.execute("SELECT * FROM security_scans ORDER BY created_at DESC").fetchall()
        return {"scans": [dict(row) for row in rows]}

@app.get("/api/memory")
async def get_memory():
    db = get_db()
    return {"preferences": db.get_preferences()}

@app.get("/api/agent-logs")
async def get_agent_logs(limit: int = 50):
    db = get_db()
    with db.get_connection() as conn:
        rows = conn.execute("SELECT * FROM agent_logs ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
        return {"logs": [dict(row) for row in rows]}

@app.get("/api/logs")
async def sse_logs(request: Request):
    queue = asyncio.Queue(maxsize=100)
    sse_queues.add(queue)
    
    async def event_generator():
        try:
            yield f"event: connected\ndata: {json.dumps({'message': 'SSE connection established'})}\n\n"
            while True:
                if await request.is_disconnected():
                    break
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=30.0)
                    event_name = event.get("event", "log")
                    data_str = json.dumps(event.get("data", {}), ensure_ascii=False)
                    yield f"event: {event_name}\ndata: {data_str}\n\n"
                except asyncio.TimeoutError:
                    hb_data = json.dumps({"timestamp": datetime.datetime.now().isoformat()})
                    yield f"event: heartbeat\ndata: {hb_data}\n\n"
        finally:
            sse_queues.discard(queue)
            
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")
