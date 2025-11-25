import asyncio
import redis
from datetime import datetime
from app.services.scoring_service import ScoringService
from app.services.logging_service import LoggingService
from app.services.data_service import DataService
from app.adapters.mock_adapter import MockLiveAdapter
from app.adapters.tiktok_adapter import TikTokLiveAdapter
from app.models.base import AsyncSessionLocal
from app.models.session import LiveSession, SessionStatus
from sqlalchemy.future import select
import uuid


class GameManager:
    def __init__(self):
        # Redis Connection
        self.redis = redis.Redis(host="redis", port=6379, decode_responses=True)

        # Services
        self.logging_service = LoggingService()
        self.data_service = DataService()
        self.current_session_id = None
        self.target_tiktok_id = None
        self.scoring_service = None

        # State Variables
        self.is_connected = False
        self.is_paused = False
        self.is_scoring_active = False
        self.current_question = None
        self.recent_logs = []  # Store recent logs for WebSocket
        self.adapter_task = None
        self.adapter = None

        # Wire up logging callback
        self.logging_service.set_callback(self.on_service_log)

    def on_service_log(self, level: str, message: str, details: dict = None):
        """Callback from LoggingService to push logs to WebSocket"""
        log_type = "System"
        if details and "type" in details:
            log_type = details["type"]

        # Push to WebSocket buffer directly
        self.add_log(level, message, log_type)

    def add_log(self, level: str, message: str, log_type: str = "System"):
        """Add a log entry to be broadcasted via WebSocket"""
        log_entry = {
            "time": datetime.now().strftime("%H:%M:%S"),
            "level": level,
            "type": log_type,
            "message": message,
        }
        self.recent_logs.append(log_entry)
        # Keep only last 50 logs in memory
        if len(self.recent_logs) > 50:
            self.recent_logs.pop(0)

    def get_and_clear_logs(self):
        """Get recent logs and clear them (for WebSocket consumption)"""
        logs = self.recent_logs[:]
        self.recent_logs = []
        return logs

    async def set_current_question(
        self,
        user_id: str,
        nickname: str,
        avatar_url: str,
        content: str,
        comment_id: int = None,
    ):
        self.current_question = {
            "user_id": user_id,
            "nickname": nickname,
            "avatar_url": avatar_url,
            "content": content,
            "timestamp": datetime.now().isoformat(),
        }

        if comment_id:
            # Mark as used in DB
            await self.data_service.mark_comment_as_used(comment_id)
            # Increment used count in Redis (for Leaderboard)
            if self.scoring_service:
                self.scoring_service.increment_used_comments(user_id)

        return self.current_question

    def get_current_question(self):
        return self.current_question

    def clear_current_question(self):
        self.current_question = None
        return {"status": "cleared"}

    async def set_session(
        self, session_id: str, reset: bool = False, channel_name: str = None
    ):
        """เปลี่ยน Session หรือ Reset"""
        # If session_id is "new", generate a UUID
        if session_id == "new":
            session_id = uuid.uuid4().hex

        self.current_session_id = session_id
        self.scoring_service = ScoringService(self.redis, self.current_session_id)

        if reset:
            keys = self.redis.keys(f"session:{session_id}:*")
            if keys:
                self.redis.delete(*keys)

        # Create or Update Session in DB
        try:
            async with AsyncSessionLocal() as session:
                existing = await session.get(LiveSession, session_id)
                if not existing:
                    new_session = LiveSession(
                        id=session_id,
                        channel_name=channel_name,
                        status=SessionStatus.STREAMING,
                    )
                    session.add(new_session)
                    await session.commit()
                    self.add_log("INFO", f"Created new session: {session_id}", "System")
                else:
                    # Resume: Update status to STREAMING if it was CLOSED
                    if existing.status == SessionStatus.CLOSED:
                        existing.status = SessionStatus.STREAMING
                        existing.end_time = None  # Clear end time
                        await session.commit()

                    self.add_log("INFO", f"Resumed session: {session_id}", "System")
        except Exception as e:
            print(f"DB Error in set_session: {e}")

        return {"status": "ok", "session_id": session_id, "reset": reset}

    async def start_stream(self, target_id: str, mode: str = "live"):
        """เริ่มเชื่อมต่อ TikTok"""
        if self.is_connected and not self.is_paused:
            return {"status": "already_connected"}

        # Auto-generate session if not set
        # Auto-generate session if not set (should be handled by set_session("new"))
        if not self.current_session_id:
            await self.set_session("new", channel_name=target_id)

        # Save last channel name
        self.redis.set("last_channel_name", target_id)

        # Update channel name in DB if not set
        try:
            async with AsyncSessionLocal() as session:
                existing = await session.get(LiveSession, self.current_session_id)
                if existing and not existing.channel_name:
                    existing.channel_name = target_id
                    await session.commit()
        except Exception as e:
            print(f"DB Error updating channel name: {e}")

        self.target_tiktok_id = target_id
        self.is_connected = True
        self.is_paused = False
        self.is_scoring_active = True

        self.add_log(
            "INFO",
            f"Starting stream for {target_id} (Session: {self.current_session_id})",
            "System",
        )

        if mode == "mock":
            self.adapter = MockLiveAdapter(
                self.scoring_service, self.data_service, "mock_data.jsonl"
            )
            self.adapter_task = asyncio.create_task(
                self.adapter.simulate_from_file(speed_multiplier=2.0)
            )
        else:
            self.adapter = TikTokLiveAdapter(
                self.scoring_service,
                self.logging_service,
                self.data_service,
                target_id,
                self.current_session_id,
            )
            self.adapter_task = asyncio.create_task(self.adapter.start())

        return {
            "status": "started",
            "mode": mode,
            "session_id": self.current_session_id,
        }

    async def pause_stream(self):
        """หยุด Data Ingestion ชั่วคราว"""
        if not self.is_connected or self.is_paused:
            return {"status": "not_connected_or_already_paused"}

        if self.adapter:
            if hasattr(self.adapter, "stop"):
                await self.adapter.stop()
            else:
                await self.adapter.stop()

        self.is_paused = True
        self.add_log("INFO", "Stream paused", "System")
        return {"status": "paused"}

    async def resume_stream(self):
        """กลับมาเชื่อมต่อใหม่ด้วย Session เดิม"""
        if not self.is_paused or not self.target_tiktok_id:
            return {"status": "cannot_resume"}

        return await self.start_stream(self.target_tiktok_id)

    async def stop_stream(self):
        """หยุดการเชื่อมต่อและเคลียร์ Session"""
        if self.adapter:
            if hasattr(self.adapter, "stop"):
                await self.adapter.stop()

            if self.adapter_task:
                self.adapter_task.cancel()

        # Update DB status to CLOSED
        if self.current_session_id:
            try:
                async with AsyncSessionLocal() as session:
                    existing = await session.get(LiveSession, self.current_session_id)
                    if existing:
                        existing.status = SessionStatus.CLOSED
                        existing.end_time = datetime.utcnow()
                        await session.commit()
            except Exception as e:
                print(f"DB Error closing session: {e}")

        self.adapter = None
        self.adapter_task = None
        self.is_connected = False
        self.is_paused = False
        self.is_scoring_active = False
        # Do NOT clear current_session_id immediately to allow reviewing stats
        # self.current_session_id = None

        self.add_log("INFO", "Stream stopped and session closed", "System")
        return {"status": "stopped"}

    def toggle_scoring(self, active: bool):
        self.is_scoring_active = active
        return {"is_scoring_active": self.is_scoring_active}

    def get_leaderboard(self):
        if not self.scoring_service:
            return []
        return self.scoring_service.get_leaderboard()

    def select_winner(self):
        if not self.scoring_service:
            return None

        self.is_scoring_active = False

        top_list = self.scoring_service.get_leaderboard()
        if not top_list:
            return None

        winner_entry = top_list[0]
        user_key = winner_entry["user_key"]
        user_id, nickname = user_key.split("|", 1)

        stats = self.scoring_service.get_user_stats_and_comments(user_id)

        self.add_log(
            "INFO",
            f"Winner selected: {nickname} ({user_id}) with score {winner_entry['score']}",
            "System",
        )

        return {
            "user_id": user_id,
            "nickname": nickname,
            "score": winner_entry["score"],
            "stats": stats.get("stats", {}),
            "comments": stats.get("comments", []),
            "gifts_breakdown": stats.get("gifts_breakdown", {}),
        }

    async def get_user_info(self, user_id: str):
        """ดึงข้อมูล User และ Comment History"""
        if not self.current_session_id:
            return None

        # Get basic stats from Redis
        stats = self.scoring_service.get_user_stats_and_comments(user_id)

        # Get detailed comments from DB (via DataService)
        db_comments = await self.data_service.get_user_comments(
            user_id, self.current_session_id
        )

        return {
            "stats": stats.get("stats", {}),
            "comments": [
                {
                    "id": c.id,
                    "content": c.content,
                    "timestamp": c.timestamp.isoformat(),
                    "is_used": c.is_used,
                }
                for c in db_comments
            ],
            "gifts_breakdown": stats.get("gifts_breakdown", {}),
        }

    async def reset_user_score(self, user_id: str):
        """Reset คะแนน User และ Mark comments as used"""
        if not self.scoring_service:
            return

        # 1. Reset Redis Stats (Move to Used)
        self.scoring_service.reset_user_stats(user_id)

        # 2. Mark comments as used in DB
        db_comments = await self.data_service.get_user_comments(
            user_id, self.current_session_id
        )
        for comment in db_comments:
            await self.data_service.mark_comment_as_used(comment.id)

        self.add_log("INFO", f"Reset score for user {user_id}", "System")

        # 3. If current question belongs to this user, clear it (Fade out overlay)
        if self.current_question and self.current_question.get("user_id") == user_id:
            self.clear_current_question()

        return {"status": "reset"}

    async def unmark_comment_as_used(self, user_id: str, comment_id: int):
        """Unmark comment as used (Restore to unused)"""
        # 1. Unmark in DB
        await self.data_service.unmark_comment_as_used(comment_id)

        # 2. Decrement used count in Redis
        if self.scoring_service:
            self.scoring_service.decrement_used_comments(user_id)

        return {"status": "unmarked"}

    async def get_recent_sessions(self):
        """Get list of recent sessions (Closed)"""
        try:
            async with AsyncSessionLocal() as session:
                result = await session.execute(
                    select(LiveSession)
                    .order_by(LiveSession.start_time.desc())
                    .limit(20)
                )
                sessions = result.scalars().all()
                return [
                    {
                        "id": s.id,
                        "channel_name": s.channel_name,
                        "start_time": (
                            s.start_time.isoformat() if s.start_time else None
                        ),
                        "end_time": s.end_time.isoformat() if s.end_time else None,
                        "status": s.status,
                        "total_score": s.total_score,
                    }
                    for s in sessions
                ]
        except Exception as e:
            print(f"Error fetching recent sessions: {e}")
            return []

    async def get_session_details(self, session_id: str):
        """Get details for a specific session (for review)"""
        # Re-use ScoringService logic but with a specific session_id
        temp_scoring = ScoringService(self.redis, session_id)
        leaderboard = temp_scoring.get_leaderboard()

        # Get basic info from DB
        session_info = {}
        try:
            async with AsyncSessionLocal() as session:
                s = await session.get(LiveSession, session_id)
                if s:
                    session_info = {
                        "id": s.id,
                        "channel_name": s.channel_name,
                        "start_time": (
                            s.start_time.isoformat() if s.start_time else None
                        ),
                        "status": s.status,
                    }
        except Exception as e:
            print(f"Error fetching session details: {e}")

        return {"info": session_info, "leaderboard": leaderboard}

    def get_last_channel_name(self):
        return self.redis.get("last_channel_name") or ""


game_manager = GameManager()
