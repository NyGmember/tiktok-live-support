import redis
import math

class ScoringService:
    """
    จัดการ Logic การคำนวณคะแนนและ Leaderboard
    (Hybrid Model: เก็บ Raw Stats + อัปเดต Real-time Leaderboard)
    """
    
    def __init__(self, redis_client: redis.Redis, session_id: str = "default_live"):
        self.r = redis_client
        self.session_id = session_id
        
        # Key หลักสำหรับ Leaderboard (ต้องเร็ว)
        self.leaderboard_key = f"session:{self.session_id}:leaderboard" # ZSET
        
        # Key สำหรับเก็บ "ข้อมูลดิบ" ของแต่ละ User (สำหรับข้อ 5)
        self.user_data_key_prefix = f"session:{self.session_id}:user_data" # HASH
        
        # Key สำหรับเก็บ "Unique Comments" (สำหรับข้อ 5)
        self.user_comments_key_prefix = f"session:{self.session_id}:comments" # SET

    def _get_gift_multiplier(self, coin_value: int) -> int:
        """
        คำนวณตัวคูณตามมูลค่า Coin (Logic ข้อ 3)
        """
        if coin_value <= 4: return 5
        if coin_value <= 9: return 6
        if coin_value <= 19: return 7
        if coin_value <= 49: return 8
        if coin_value <= 99: return 10
        if coin_value <= 299: return 15
        if coin_value <= 999: return 20
        return 30 # >= 1000

    def _get_user_key(self, user_id: str, user_nickname: str) -> str:
        """สร้าง Key มาตรฐานสำหรับ ZSET"""
        return f"{user_id}|{user_nickname}"

    def process_like(self, user_id: str, user_nickname: str, like_count: int, is_follower: bool):
        """
        ประมวลผล Like: 
        1. คำนวณคะแนนเป็น float
        2. อัปเดต Leaderboard (ZSET)
        3. เก็บสถิติดิบ (HASH)
        """
        
        # --- ⬇️ START MODIFICATION ⬇️ ---
        
        if is_follower:
            # 10 likes = 1 point
            points = like_count / 10.0  # <--- เปลี่ยนเป็น Float
            like_type_key = "likes_as_follower"
        else:
            # 15 likes = 1 point
            points = like_count / 15.0  # <--- เปลี่ยนเป็น Float
            like_type_key = "likes_as_non_follower"
            
        # --- ⬆️ END MODIFICATION ⬆️ ---

        if points > 0:
            # ตอนนี้ points อาจจะเป็น 0.1, 0.5, 1.2
            print(f"❤️  [{user_nickname}] (Follower: {is_follower}) got {points:.4f} points from {like_count} likes") # แสดงผล 4 ตำแหน่ง
            
            user_key = self._get_user_key(user_id, user_nickname)
            user_hash_key = f"{self.user_data_key_prefix}:{user_id}"

            # 2. อัปเดต Leaderboard (ZSET) - Redis รับ float ได้เลย
            self.r.zincrby(self.leaderboard_key, points, user_key)
            
            # 3. เก็บสถิติดิบ (HASH)
            pipe = self.r.pipeline()
            pipe.hset(user_hash_key, "nickname", user_nickname) 
            pipe.hincrby(user_hash_key, "total_likes", like_count)
            pipe.hincrby(user_hash_key, like_type_key, like_count)
            
            # เราเก็บคะแนนดิบ (float) ลงใน HASH ด้วย
            pipe.hincrbyfloat(user_hash_key, "points_from_likes", points) # <--- ใช้ HINCRBYFLOAT
            pipe.execute()

    def process_gift(self, user_id: str, user_nickname: str, 
                     coin_value_per_unit: int, 
                     gift_id: str, gift_name: str, gift_quantity: int):
        """
        ประมวลผล Gift: (ปรับปรุงใหม่)
        1. คำนวณคะแนน
        2. อัปเดต Leaderboard (ZSET)
        3. เก็บสถิติดิบ (HASH) - ทั้งแบบสรุปและแบบแยกประเภทของขวัญ
        """
        
        # 1. คำนวณคะแนน (จากมูลค่าต่อชิ้น * จำนวนชิ้น)
        # เราใช้ multiplier จาก "มูลค่าต่อชิ้น" (ตาม Logic เดิม)
        multiplier = self._get_gift_multiplier(coin_value_per_unit)
        points = (coin_value_per_unit * multiplier) * gift_quantity
        
        total_coin_value = coin_value_per_unit * gift_quantity
        
        print(f"🎁 [{user_nickname}] got {points} points from {gift_quantity}x {gift_name} ({total_coin_value} coins total)")
        
        user_key = self._get_user_key(user_id, user_nickname)
        
        # --- Key Definitions ---
        user_summary_hash_key = f"{self.user_data_key_prefix}:{user_id}" # HASH สรุป
        user_gifts_hash_key = f"session:{self.session_id}:user_gifts:{user_id}" # HASH เก็บยอดของขวัญ
        
        # 2. อัปเดต Leaderboard (ZSET)
        self.r.zincrby(self.leaderboard_key, points, user_key)
        
        # 3. เก็บสถิติดิบ (HASH)
        pipe = self.r.pipeline()
        
        # --- 3a. อัปเดต HASH สรุป (Summary) ---
        pipe.hset(user_summary_hash_key, "nickname", user_nickname)
        pipe.hincrby(user_summary_hash_key, "total_gift_coins", total_coin_value)
        # แก้ไข: นับจำนวน "ชิ้น" ที่ส่ง ไม่ใช่ "ครั้ง"
        pipe.hincrby(user_summary_hash_key, "total_gifts_sent", gift_quantity) 
        pipe.hincrbyfloat(user_summary_hash_key, "points_from_gifts", points) # ใช้ float เผื่อมี
        
        # --- 3b. อัปเดต HASH ของขวัญ (Detailed) ---
        # เราจะเก็บยอดรวมของขวัญแต่ละชนิด โดยใช้ Key = "gift_id|gift_name"
        gift_field_key = f"{gift_id}|{gift_name}"
        pipe.hincrby(user_gifts_hash_key, gift_field_key, gift_quantity)
        
        pipe.execute()

    def process_comment(self, user_id: str, comment_text: str):
        """
        เก็บ Unique Comment ของ User (Logic ข้อ 5)
        """
        comment_key = f"{self.user_comments_key_prefix}:{user_id}"
        
        # SADD: trả về 1 nếu là item mới, 0 nếu đã có
        if self.r.sadd(comment_key, comment_text):
            print(f"💬 Saved NEW comment for {user_id}: {comment_text}")
            # อัปเดต HASH ด้วย (Optional)
            user_hash_key = f"{self.user_data_key_prefix}:{user_id}"
            self.r.hincrby(user_hash_key, "unique_comments_count", 1)


    # ==================================================================
    # == ส่วนของการ "แสดงผล" (คำนวณจาก ZSET ที่เตรียมไว้แล้ว) ==
    # ==================================================================

    def get_top_5_leaderboard(self) -> list:
        """
        ดึง Top 5 Leaderboard (สำหรับข้อ 4)
        ดึงจาก ZSET (ซึ่งเป็น float) แล้วปัดเศษลง
        """
        top_5 = self.r.zrevrange(self.leaderboard_key, 0, 4, withscores=True)
        
        return [
            {
                "user_key": item[0], 
                "score": int(item[1])  # <--- ปัดเศษลง (floor) ตรงนี้
            }
            for item in top_5
        ]

    # ==================================================================
    # == ส่วนของการ "แสดงที่มา" (คำนวณจาก HASH) ==
    # ==================================================================

    def get_user_stats_and_comments(self, user_id: str) -> dict:
        """
        ดึงสถิติที่มาของคะแนน (ข้อ 5) และ Comments (ข้อ 6)
        (ปรับปรุงใหม่: เพิ่มการดึงข้อมูลของขวัญ)
        """
        user_summary_hash_key = f"{self.user_data_key_prefix}:{user_id}"
        comments_key = f"{self.user_comments_key_prefix}:{user_id}"
        user_gifts_hash_key = f"session:{self.session_id}:user_gifts:{user_id}" # Key ใหม่
        
        # 1. ดึงสถิติดิบ (HGETALL)
        stats_raw = self.r.hgetall(user_summary_hash_key)
        stats = {k: v for k, v in stats_raw.items()}
        
        # 2. ดึง Comments (SMEMBERS)
        comments_raw = self.r.smembers(comments_key)
        comments = [c for c in comments_raw]
        
        # 3. ดึงสถิติของขวัญ (HGETALL)
        gifts_raw = self.r.hgetall(user_gifts_hash_key)
        gifts_breakdown = {}
        for k, v in gifts_raw.items():
            key_parts = k.split('|', 1)
            gift_id = key_parts[0]
            gift_name = key_parts[1] if len(key_parts) > 1 else "Unknown Gift"
            
            gifts_breakdown[gift_name] = {
                "id": gift_id,
                "count": int(v)
            }

        return {
            "stats": stats,
            "comments": comments,
            "gifts_breakdown": gifts_breakdown  # <-- เพิ่มส่วนนี้
        }