import asyncio
import redis
from app.services.scoring_service import ScoringService
from app.adapters.mock_adapter import MockLiveAdapter
# from app.adapters.tiktok_adapter import TikTokLiveAdapter (ในอนาคต)

class GameManager:
    def __init__(self):
        # Redis Connection
        self.redis = redis.Redis(host='redis', port=6379, decode_responses=True)
        
        # State Variables
        self.current_session_id = "default"
        self.scoring_service = ScoringService(self.redis, self.current_session_id)
        
        self.is_connected = False
        self.is_scoring_active = False # ปุ่มหยุดรับคำถาม
        self.adapter_task = None # เก็บ Task ของ asyncio เพื่อสั่ง Cancel ได้
        self.adapter = None

    def set_session(self, session_id: str, reset: bool = False):
        """เปลี่ยน Session หรือ Reset"""
        self.current_session_id = session_id
        # Re-init service with new session
        self.scoring_service = ScoringService(self.redis, self.current_session_id)
        
        if reset:
            # ล้างข้อมูลใน Redis ของ Session นี้
            keys = self.redis.keys(f"session:{session_id}:*")
            if keys:
                self.redis.delete(*keys)
        
        return {"status": "ok", "session_id": session_id, "reset": reset}

    async def start_stream(self, target_id: str, mode: str = "mock"):
        """เริ่มเชื่อมต่อ TikTok หรือ Mock"""
        if self.is_connected:
            return {"status": "already_connected"}

        self.is_connected = True
        self.is_scoring_active = True # เริ่มมาให้เก็บคะแนนเลย หรือจะรอสั่งก็ได้

        if mode == "mock":
            # ใช้ Mock Adapter
            self.adapter = MockLiveAdapter(self.scoring_service, "mock_data.jsonl")
            # Run ใน Background Loop ไม่ให้ Block API
            self.adapter_task = asyncio.create_task(self.adapter.simulate_from_file(speed_multiplier=2.0))
        else:
            # TODO: ใส่ TikTokAdapter ของจริงตรงนี้
            pass

        return {"status": "started", "mode": mode}

    async def stop_stream(self):
        """หยุดการเชื่อมต่อ"""
        if self.adapter_task:
            self.adapter_task.cancel() # สั่งหยุด Loop
            try:
                await self.adapter_task
            except asyncio.CancelledError:
                pass
            self.adapter_task = None
        
        self.is_connected = False
        self.is_scoring_active = False
        return {"status": "stopped"}

    def toggle_scoring(self, active: bool):
        """ปุ่มหยุดรับคำถาม (Stop Collecting Answers)"""
        self.is_scoring_active = active
        # เราต้องส่ง flag นี้ไปบอก ScoringService ด้วย (ต้องไปเพิ่ม flag ใน class ScoringService)
        # หรือใน Adapter ให้เช็คค่านี้ก่อนเรียก process_xxx
        return {"is_scoring_active": self.is_scoring_active}

    def get_leaderboard(self):
        return self.scoring_service.get_top_5_leaderboard()

    def select_winner(self):
        """
        Logic ข้อ 5: 
        1. หยุดรับคะแนนทันที
        2. ดึงคนคะแนนสูงสุด
        3. ลบคนนั้นออกจาก Leaderboard (เพื่อให้คนอื่นขึ้นมาแทนในรอบหน้า)
        4. คืนค่า Stats
        """
        self.is_scoring_active = False # หยุดรับคะแนน
        
        # ดึง Top 1
        top_list = self.scoring_service.get_top_5_leaderboard()
        if not top_list:
            return None

        winner_entry = top_list[0]
        user_key = winner_entry['user_key']
        user_id, nickname = user_key.split('|', 1)
        
        # ดึงข้อมูลดิบ
        stats = self.scoring_service.get_user_stats_and_comments(user_id)
        
        # ลบออกจาก Leaderboard (ZREM)
        self.redis.zrem(self.scoring_service.leaderboard_key, user_key)

        return {
            "user_id": user_id,
            "nickname": nickname,
            "score": winner_entry['score'],
            "stats": stats['stats'],
            "comments": stats['comments'],
            "gifts_breakdown": stats['gifts_breakdown']
        }

# สร้าง Global Instance ไว้ใช้งาน
game_manager = GameManager()