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

# --- 3. Game Actions ---
@app.post("/winner/select", response_model=WinnerResponse)
async def select_winner():
    """กดปุ่ม 'เฉลย/เลือกผู้ชนะ'"""
    winner = game_manager.select_winner()
    if not winner:
        raise HTTPException(status_code=404, detail="No winner found or leaderboard empty")
    return winner

@app.get("/status", response_model=SystemStatus)
async def get_status():
    """ดึงสถานะระบบ"""
    return {
        "is_connected": game_manager.is_connected,
        "is_scoring_active": game_manager.is_scoring_active,
        "current_session_id": game_manager.current_session_id,
        "target_tiktok_id": game_manager.adapter.unique_id if game_manager.adapter and hasattr(game_manager.adapter, 'unique_id') else "@mock"
    }

# ================= WEBSOCKET (Real-time Leaderboard) =================
@app.websocket("/ws/leaderboard")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = game_manager.get_leaderboard()
            await websocket.send_text(json.dumps(data))
            await asyncio.sleep(0.5)
    except WebSocketDisconnect:
        print("Client disconnected")