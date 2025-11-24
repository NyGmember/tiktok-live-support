import json
import time
import asyncio
from app.services.scoring_service import ScoringService


class MockLiveAdapter:
    """
    จำลองการยิง Event จากไฟล์ .jsonl ที่บันทึกไว้
    """

    def __init__(
        self, scoring_service: ScoringService, data_service, mock_file_path: str
    ):
        self.service = scoring_service
        self.data_service = data_service
        self.file_path = mock_file_path
        self.is_scoring_active = True
        self.is_running = False

    def set_scoring(self, active: bool):
        self.is_scoring_active = active

    async def stop(self):
        self.is_running = False
        print("Mock Adapter Stopped")

    async def simulate_from_file(self, speed_multiplier: float = 1.0):
        """
        เริ่มการจำลองโดยการอ่านไฟล์
        """
        self.is_running = True
        print(
            f"========= 🚀 MOCK SIMULATION START (Session: {self.service.session_id}) ========= "
        )
        print(f"Reading from {self.file_path}...")

        try:
            while self.is_running:
                with open(self.file_path, "r", encoding="utf-8") as f:
                    for line in f:
                        if not self.is_running:
                            break
                        if not line.strip():
                            continue

                        # ก่อนเรียก self.service.process_xxx
                        if not self.is_scoring_active:
                            continue  # ข้าม Event นี้ไปเลยถ้าปิดรับคะแนนอยู่

                        try:
                            event = json.loads(line)
                            event_type = event.get("type")
                            payload = event.get("payload")

                            # Simulate delay if needed (optional)
                            await asyncio.sleep(0.1 / speed_multiplier)

                            if event_type == "comment":
                                user_info = payload.get("userInfo", {})
                                user_id = user_info.get("id")
                                nickname = user_info.get("nickName")
                                avatar_url = user_info.get("avatarThumb", {}).get(
                                    "mUrls", [""]
                                )[0]
                                comment = payload.get("content")

                                if user_id and comment:
                                    await self.data_service.upsert_user(
                                        user_id, nickname, avatar_url
                                    )
                                    await self.data_service.save_comment(
                                        user_id, comment, self.service.session_id
                                    )
                                    self.service.process_comment(
                                        user_id, comment, nickname, avatar_url
                                    )

                            elif event_type == "like":
                                user = payload.get("user", {})
                                user_id = user.get("id")
                                nickname = user.get("nickName")
                                avatar_url = user.get("avatarThumb", {}).get(
                                    "urlList", [""]
                                )[0]
                                is_follower = (
                                    user.get("follow_info", {}).get("follow_status", 0)
                                    == 1
                                )
                                like_count = payload.get("count", 0)

                                if user_id and nickname and like_count > 0:
                                    await self.data_service.upsert_user(
                                        user_id, nickname, avatar_url
                                    )
                                    self.service.process_like(
                                        user_id,
                                        nickname,
                                        like_count,
                                        is_follower,
                                        avatar_url,
                                    )

                            elif event_type == "gift":
                                user = payload.get("fromUser", {})
                                user_id = user.get("id")
                                nickname = user.get("nickName")
                                avatar_url = user.get("avatarThumb", {}).get(
                                    "mUrls", [""]
                                )[0]

                                gift_info = payload.get("mGift", {})
                                coin_value_per_unit = gift_info.get("diamondCount", 0)
                                gift_id = gift_info.get("id", "Unknown")
                                gift_name = gift_info.get("name", "Unknown Gift")
                                gift_quantity = payload.get("repeatCount", 1)

                                if (
                                    user_id
                                    and nickname
                                    and coin_value_per_unit > 0
                                    and gift_quantity > 0
                                ):
                                    await self.data_service.upsert_user(
                                        user_id, nickname, avatar_url
                                    )
                                    await self.data_service.save_gift(
                                        user_id,
                                        gift_id,
                                        gift_name,
                                        coin_value_per_unit,
                                        gift_quantity,
                                        self.service.session_id,
                                    )

                                    self.service.process_gift(
                                        user_id,
                                        nickname,
                                        coin_value_per_unit,
                                        gift_id,
                                        gift_name,
                                        gift_quantity,
                                        avatar_url,
                                    )

                        except json.JSONDecodeError:
                            print(f"Warning: Skipping malformed line: {line}")
                        except Exception as e:
                            print(f"Error processing event: {e} | Data: {line}")

                if self.is_running:
                    print("========= MOCK LOOP RESTARTING ========= ")
                    await asyncio.sleep(1)

            print("========= MOCK SIMULATION FINISHED ========= ")

        except FileNotFoundError:
            print(f"Error: Mock data file not found at {self.file_path}")
