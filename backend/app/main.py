from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import json
from contextlib import asynccontextmanager

from app.game_manager import game_manager
from app.schemas import SessionRequest, SystemStatus, WinnerResponse
from app.models.base import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("Initializing Database...")
    try:
        await init_db()
        print("Database Initialized.")
    except Exception as e:
        print(f"Database Initialization Failed: {e}")

    yield

    # Shutdown
    await game_manager.stop_stream()


app = FastAPI(title="TikTok Live Support System", lifespan=lifespan)

# --- CORS Setting ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ================= API ENDPOINTS =================


@app.get("/")
async def root():
    return {"message": "TikTok Live API is running"}


# --- 1. Session Management ---
@app.post("/session/set")
async def set_session(req: SessionRequest):
    """ตั้งค่า Session ใหม่ หรือ Reset"""
    return await game_manager.set_session(req.session_id, req.reset_scores)


# --- 2. Control System (Start/Stop Live) ---
@app.post("/control/start")
async def start_stream(target_id: str = "@test", mode: str = "mock"):
    """เริ่มรับข้อมูล (เชื่อมต่อ TikTok/Mock)"""
    return await game_manager.start_stream(target_id, mode)


@app.post("/control/stop")
async def stop_stream():
    """ตัดการเชื่อมต่อ"""
    return await game_manager.stop_stream()


@app.post("/control/scoring/{active}")
async def set_scoring(active: bool):
    """เปิด/ปิด การรับคะแนน"""
    return game_manager.toggle_scoring(active)


from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import json
from contextlib import asynccontextmanager
from pydantic import BaseModel

from app.game_manager import game_manager
from app.schemas import SessionRequest, SystemStatus, WinnerResponse
from app.models.base import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("Initializing Database...")
    try:
        await init_db()
        print("Database Initialized.")
    except Exception as e:
        print(f"Database Initialization Failed: {e}")

    yield

    # Shutdown
    await game_manager.stop_stream()


app = FastAPI(title="TikTok Live Support System", lifespan=lifespan)

# --- CORS Setting ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ================= API ENDPOINTS =================


@app.get("/")
async def root():
    return {"message": "TikTok Live API is running"}


# --- 1. Session Management ---
@app.post("/session/set")
async def set_session(req: SessionRequest):
    """ตั้งค่า Session ใหม่ หรือ Reset"""
    return await game_manager.set_session(req.session_id, req.reset_scores)


# --- 2. Control System (Start/Stop Live) ---
# Removed old /control/start, /control/stop, /control/scoring/{active}


class StreamRequest(BaseModel):
    tiktok_username: str
    mode: str = "mock"


@app.post("/stream/start")
async def start_stream(request: StreamRequest):
    return await game_manager.start_stream(request.tiktok_username, request.mode)


@app.post("/stream/stop")
async def stop_stream():
    return await game_manager.stop_stream()


@app.post("/stream/pause")
async def pause_stream():
    return await game_manager.pause_stream()


@app.post("/stream/resume")
async def resume_stream():
    return await game_manager.resume_stream()


@app.post("/game/winner")
def select_winner():
    winner = game_manager.select_winner()
    if not winner:
        raise HTTPException(status_code=404, detail="No winner found")
    return winner


@app.get("/user/{user_id}")
async def get_user_info(user_id: str):
    info = await game_manager.get_user_info(user_id)
    if not info:
        raise HTTPException(
            status_code=404, detail="User not found or no active session"
        )
    return info


@app.post("/user/{user_id}/reset")
async def reset_user_score(user_id: str):
    return await game_manager.reset_user_score(user_id)


class QuestionRequest(BaseModel):
    user_id: str
    nickname: str
    avatar_url: str
    content: str


@app.post("/question")
def set_question(request: QuestionRequest):
    return game_manager.set_current_question(
        request.user_id, request.nickname, request.avatar_url, request.content
    )


@app.get("/question")
def get_question():
    return game_manager.get_current_question()


@app.delete("/question")
def clear_question():
    return game_manager.clear_current_question()


@app.get("/status")
def get_status():
    return {
        "is_connected": game_manager.is_connected,
        "is_paused": game_manager.is_paused,
        "is_scoring_active": game_manager.is_scoring_active,
        "session_id": game_manager.current_session_id,
        "target_id": game_manager.target_tiktok_id,
    }


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = game_manager.get_leaderboard()
            question = game_manager.get_current_question()
            logs = game_manager.get_and_clear_logs()

            await websocket.send_json(
                {
                    "leaderboard": data,
                    "question": question,
                    "logs": logs,
                    "status": {
                        "is_connected": game_manager.is_connected,
                        "is_paused": game_manager.is_paused,
                        "session_id": game_manager.current_session_id,
                    },
                }
            )
            await asyncio.sleep(1)
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        await websocket.close()
