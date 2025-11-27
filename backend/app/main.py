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
    # Note: req.session_id can be "new"
    return await game_manager.set_session(req.session_id, req.reset_scores)


@app.get("/sessions/history")
async def get_session_history():
    return await game_manager.get_recent_sessions()


@app.get("/sessions/{session_id}")
async def get_session_details(session_id: str):
    return await game_manager.get_session_details(session_id)


@app.get("/sessions/{session_id}/users/{user_id}")
async def get_session_user_details(session_id: str, user_id: str):
    return await game_manager.get_session_user_details(session_id, user_id)


@app.get("/channel/last")
def get_last_channel():
    return {"channel_name": game_manager.get_last_channel_name()}


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
    comment_id: int = None


@app.post("/question")
async def set_question(request: QuestionRequest):
    return await game_manager.set_current_question(
        request.user_id,
        request.nickname,
        request.avatar_url,
        request.content,
        request.comment_id,
    )


@app.post("/comment/{comment_id}/unuse")
async def unuse_comment(comment_id: int, user_id: str):
    return await game_manager.unmark_comment_as_used(user_id, comment_id)


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
            # Check if client disconnected
            # if websocket.client_state == WebSocket.client_state.DISCONNECTED:
            #    break

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
    except WebSocketDisconnect:
        print("WebSocket disconnected")
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        try:
            await websocket.close()
        except RuntimeError:
            pass  # Already closed
