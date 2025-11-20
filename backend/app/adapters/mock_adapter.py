import json
import time
import asyncio
from app.services.scoring_service import ScoringService

class MockLiveAdapter:
    """
    จำลองการยิง Event จากไฟล์ .jsonl ที่บันทึกไว้
    """
    
    def __init__(self, scoring_service: ScoringService, mock_file_path: str):
        self.service = scoring_service
        self.file_path = mock_file_path
        self.is_scoring_active = True 
        
    def set_scoring(self, active: bool):
        self.is_scoring_active = active

    async def simulate_from_file(self, speed_multiplier: float = 1.0):
        """
        เริ่มการจำลองโดยการอ่านไฟล์
        """
        print(f"========= 🚀 MOCK SIMULATION START (Session: {self.service.session_id}) ========= ")
        print(f"Reading from {self.file_path}...")
        
        last_event_time = None
        
        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                for line in f:
                    if not line.strip():
                        continue
                    
                    # ก่อนเรียก self.service.process_xxx
                    if not self.is_scoring_active:
                        continue # ข้าม Event นี้ไปเลยถ้าปิดรับคะแนนอยู่
                        
                    try:
                        event = json.loads(line)
                        event_type = event.get("type")
                        payload = event.get("payload")
                        # --- Logic การหน่วงเวลาให้เหมือนจริง ---
                        # current_event_time = event.get("timestamp")
                        # if last_event_time:
                        #     delay = (current_event_time - last_event_time) / speed_multiplier
                        #     if delay > 0:
                        #         await asyncio.sleep(delay)
                        # last_event_time = current_event_time
                        # -------------------------------------

                        if event_type == "comment":
                            user_id = payload.get("userInfo", {}).get("id")
                            comment = payload.get("content")
                            if user_id and comment:
                                self.service.process_comment(user_id, comment)

                        elif event_type == "like":
                            user = payload.get("user", {})
                            user_id = user.get("id")
                            nickname = user.get("nickName")
                            is_follower = user.get("follow_info", {}).get("follow_status", 0) == 1 # 1=Follow, 0=Not
                            like_count = payload.get("count", 0)
                            
                            if user_id and nickname and like_count > 0:
                                self.service.process_like(user_id, nickname, like_count, is_follower)

                        elif event_type == "gift":
                            user = payload.get("fromUser", {})
                            user_id = user.get("id")
                            nickname = user.get("nickName")
                            
                            gift_info = payload.get("mGift", {})
                            
                            # มูลค่าต่อ 1 ชิ้น
                            coin_value_per_unit = gift_info.get("diamondCount", 0) 
                            
                            # ID และ ชื่อ
                            gift_id = gift_info.get("id", "Unknown")
                            gift_name = gift_info.get("name", "Unknown Gift")
                            
                            # จำนวนชิ้นที่ส่งใน Event นี้ (สำคัญมาก)
                            # ใน TikTokLive Event, 'count' คือจำนวนชิ้น
                            gift_quantity = payload.get("repeatCount", 1)
                            gift_stackable = gift_info.get("combo", True)
                            gift_combo_count = payload.get("comboCount", 1)

                            if user_id and nickname and coin_value_per_unit > 0 and gift_quantity > 0:
                                # เรียกใช้ Signature ใหม่
                                self.service.process_gift(
                                    user_id, 
                                    nickname, 
                                    coin_value_per_unit,
                                    gift_id,
                                    gift_name,
                                    gift_quantity
                                )

                    except json.JSONDecodeError:
                        print(f"Warning: Skipping malformed line: {line}")
                    except Exception as e:
                        print(f"Error processing event: {e} | Data: {line}")
                        
            print("========= MOCK SIMULATION FINISHED ========= ")

        except FileNotFoundError:
            print(f"Error: Mock data file not found at {self.file_path}")