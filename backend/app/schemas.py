from pydantic import BaseModel
from typing import List, Optional, Dict

# รับ Request สร้าง/เลือก Session
class SessionRequest(BaseModel):
    session_id: str
    reset_scores: bool = False

# ส่งข้อมูล Leaderboard กลับไปแสดงผล
class LeaderboardEntry(BaseModel):
    user_key: str
    score: int

# ส่งข้อมูล Winner กลับไป (Stats + Comments)
class WinnerResponse(BaseModel):
    user_id: str
    nickname: str
    score: int
    stats: Dict[str, str]
    comments: List[str]
    gifts_breakdown: Dict[str, Dict[str, int]]

# Status ของระบบ (เพื่อโชว์หน้า Admin ว่าระบบสถานะเป็นยังไง)
class SystemStatus(BaseModel):
    is_connected: bool
    is_scoring_active: bool
    current_session_id: str
    target_tiktok_id: Optional[str]