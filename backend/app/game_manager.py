import asyncio
import redis
from datetime import datetime
from app.services.scoring_service import ScoringService
from app.services.logging_service import LoggingService
from app.adapters.mock_adapter import MockLiveAdapter
from app.adapters.tiktok_adapter import TikTokLiveAdapter
from app.models.base import AsyncSessionLocal
from app.models.session import LiveSession

class GameManager:
    def __init__(self):
        # Redis Connection
        # Ensure we use the hostname 'redis' as defined in docker-compose
        self.redis = redis.Redis(host='redis', port=6379, decode_responses=True)
        
        # Services
        self.logging_service = LoggingService()
        self.current_session_id = "default"
        self.scoring_service = ScoringService(self.redis, self.current_session_id)
        
        # State Variables
        self.is_connected = False
        self.is_scoring_active = False
        self.adapter_task = None
        self.adapter = None

    async def set_session(self, session_id: str, reset: bool = False):
        """เปลี่ยน Session หรือ Reset"""
        self.current_session_id = session_id
        self.scoring_service = ScoringService(self.redis, self.current_session_id)
        
        if reset:
            keys = self.redis.keys(f"session:{session_id}:*")
            if keys:
                self.redis.delete(*keys)
        
        # Create Session in DB
        try:
            async with AsyncSessionLocal() as session:
                existing = await session.get(LiveSession, session_id)
                if not existing:
                    new_session = LiveSession(id=session_id)
                    session.add(new_session)
                    await session.commit()
                    await self.logging_service.info(f"Created new session: {session_id}")
                else:
                    await self.logging_service.info(f"Resumed session: {session_id}")
        except Exception as e:
            print(f"DB Error in set_session: {e}")

        return {"status": "ok", "session_id": session_id, "reset": reset}

    async def start_stream(self, target_id: str, mode: str = "mock"):
        """เริ่มเชื่อมต่อ TikTok หรือ Mock"""
        if self.is_connected:
            return {"status": "already_connected"}

        self.is_connected = True
        self.is_scoring_active = True 
        
        await self.logging_service.info(f"Starting stream for {target_id} (Mode: {mode})")

        if mode == "mock":
            self.adapter = MockLiveAdapter(self.scoring_service, "mock_data.jsonl")
            self.adapter_task = asyncio.create_task(self.adapter.simulate_from_file(speed_multiplier=2.0))
        else:
            self.adapter = TikTokLiveAdapter(self.scoring_service, self.logging_service, target_id)
            self.adapter_task = asyncio.create_task(self.adapter.start())

        return {"status": "started", "mode": mode}

    async def stop_stream(self):
        """หยุดการเชื่อมต่อ"""
        if self.adapter:
            if isinstance(self.adapter, TikTokLiveAdapter):
                await self.adapter.stop()
            elif self.adapter_task:
                self.adapter_task.cancel()
                try:
                    await self.adapter_task
                except asyncio.CancelledError:
                    pass
            
        self.adapter = None
        self.adapter_task = None
        self.is_connected = False
        self.is_scoring_active = False
        
        await self.logging_service.info("Stream stopped")
        return {"status": "stopped"}

    def toggle_scoring(self, active: bool):
        self.is_scoring_active = active
        return {"is_scoring_active": self.is_scoring_active}

    def get_leaderboard(self):
        return self.scoring_service.get_top_5_leaderboard()

    def select_winner(self):
        self.is_scoring_active = False
        
        top_list = self.scoring_service.get_top_5_leaderboard()
        if not top_list:
            return None

        winner_entry = top_list[0]
        user_key = winner_entry['user_key']
        user_id, nickname = user_key.split('|', 1)
        
        stats = self.scoring_service.get_user_stats_and_comments(user_id)
        
        self.redis.zrem(self.scoring_service.leaderboard_key, user_key)
        
        # Log winner
        asyncio.create_task(self.logging_service.info(f"Winner selected: {nickname} ({user_id}) with score {winner_entry['score']}"))

        return {
            "user_id": user_id,
            "nickname": nickname,
            "score": winner_entry['score'],
            "stats": stats['stats'],
            "comments": stats['comments'],
            "gifts_breakdown": stats['gifts_breakdown']
        }

game_manager = GameManager()