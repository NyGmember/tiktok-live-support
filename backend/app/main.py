from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import json

from app.game_manager import game_manager
from app.schemas import SessionRequest, SystemStatus, WinnerResponse

app = FastAPI(title="TikTok Live Support System")

# --- CORS Setting (สำคัญมากเพื่อให้ Vue.js เรียก API ได้) ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Dev mode ให้ยอมรับทุกที่
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
    return game_manager.set_session(req.session_id, req.reset_scores)

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
    """
    เปิด/ปิด การรับคะแนน (ใช้คู่กับปุ่มนับถอยหลัง 5 วิ)
    Frontend นับถอยหลังจบ -> ยิง API นี้เป็น False
    """
    return game_manager.toggle_scoring(active)

# --- 3. Game Actions ---
@app.post("/winner/select", response_model=WinnerResponse)
async def select_winner():
    """
    กดปุ่ม 'เฉลย/เลือกผู้ชนะ':
    - หยุดรับคะแนน
    - ดึง Top 1 และข้อมูลทั้งหมด
    - ลบ Top 1 ออกจาก Leaderboard
    """
    winner = game_manager.select_winner()
    if not winner:
        raise HTTPException(status_code=404, detail="No winner found or leaderboard empty")
    return winner

@app.get("/status", response_model=SystemStatus)
async def get_status():
    """ดึงสถานะระบบ (สำหรับหน้า Admin)"""
    return {
        "is_connected": game_manager.is_connected,
        "is_scoring_active": game_manager.is_scoring_active,
        "current_session_id": game_manager.current_session_id,
        "target_tiktok_id": "@mock" # ในอนาคตเอามาจาก State จริง
    }

# ================= WEBSOCKET (Real-time Leaderboard) =================
@app.websocket("/ws/leaderboard")
async def websocket_endpoint(websocket: WebSocket):
    """
    ส่ง Leaderboard ไปหา Frontend ทุกๆ 0.5 วินาที
    (ดีกว่าให้ Frontend ยิง HTTP Request ถี่ๆ)
    """
    await websocket.accept()
    try:
        while True:
            # ดึง Leaderboard ล่าสุด
            data = game_manager.get_leaderboard()
            
            # ส่ง JSON ไปที่ Frontend
            await websocket.send_text(json.dumps(data))
            
            # รอ 0.5 วินาที (ปรับความถี่ได้ตามต้องการ)
            await asyncio.sleep(0.5)
    except WebSocketDisconnect:
        print("Client disconnected")