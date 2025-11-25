import redis
import math
import json
from datetime import datetime


class ScoringService:
    """
    จัดการ Logic การคำนวณคะแนนและ Leaderboard
    (Hybrid Model: เก็บ Raw Stats + อัปเดต Real-time Leaderboard)
    """

    def __init__(self, redis_client: redis.Redis, session_id: str = "default_live"):
        self.r = redis_client
        self.session_id = session_id

        # Key หลักสำหรับ Leaderboard (ต้องเร็ว)
        self.leaderboard_key = f"session:{self.session_id}:leaderboard"  # ZSET

        # Key สำหรับเก็บ "ข้อมูลดิบ" ของแต่ละ User (สำหรับข้อ 5)
        self.user_data_key_prefix = f"session:{self.session_id}:user_data"  # HASH

        # Key สำหรับเก็บ "Unique Comments" (สำหรับข้อ 5)
        self.user_comments_key_prefix = f"session:{self.session_id}:comments"  # SET

    def _get_gift_multiplier(self, coin_value: int) -> int:
        """
        คำนวณตัวคูณตามมูลค่า Coin (Logic ข้อ 3)
        """
        if coin_value <= 4:
            return 5
        if coin_value <= 9:
            return 6
        if coin_value <= 19:
            return 7
        if coin_value <= 49:
            return 8
        if coin_value <= 99:
            return 10
        if coin_value <= 299:
            return 15
        if coin_value <= 999:
            return 20


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
        self.leaderboard_key = f"session:{self.session_id}:leaderboard"  # ZSET

        # Key สำหรับเก็บ "ข้อมูลดิบ" ของแต่ละ User (สำหรับข้อ 5)
        self.user_data_key_prefix = f"session:{self.session_id}:user_data"  # HASH

        # Key สำหรับเก็บ "Unique Comments" (สำหรับข้อ 5)
        self.user_comments_key_prefix = f"session:{self.session_id}:comments"  # SET

    def _get_gift_multiplier(self, coin_value: int) -> int:
        """
        คำนวณตัวคูณตามมูลค่า Coin (Logic ข้อ 3)
        """
        if coin_value <= 4:
            return 5
        if coin_value <= 9:
            return 6
        if coin_value <= 19:
            return 7
        if coin_value <= 49:
            return 8
        if coin_value <= 99:
            return 10
        if coin_value <= 299:
            return 15
        if coin_value <= 999:
            return 20
        return 30  # >= 1000

    def _get_user_key(self, user_id: str, user_nickname: str) -> str:
        """สร้าง Key มาตรฐานสำหรับ ZSET"""
        return f"{user_id}|{user_nickname}"

    def process_like(
        self,
        user_id: str,
        user_nickname: str,
        like_count: int,
        is_follower: bool,
        avatar_url: str = None,
    ):
        """
        ประมวลผล Like:
        1. คำนวณคะแนนเป็น float
        2. อัปเดต Leaderboard (ZSET)
        3. เก็บสถิติดิบ (HASH)
        """

        if is_follower:
            # 10 likes = 1 point
            points = like_count / 10.0
            like_type_key = "likes_as_follower"
        else:
            # 15 likes = 1 point
            points = like_count / 15.0
            like_type_key = "likes_as_non_follower"

        if points > 0:
            # print(f"❤️  [{user_nickname}] (Follower: {is_follower}) got {points:.4f} points from {like_count} likes")

            user_key = self._get_user_key(user_id, user_nickname)
            user_hash_key = f"{self.user_data_key_prefix}:{user_id}"

            # 2. อัปเดต Leaderboard (ZSET)
            self.r.zincrby(self.leaderboard_key, points, user_key)

            # 3. เก็บสถิติดิบ (HASH)
            pipe = self.r.pipeline()
            pipe.hset(user_hash_key, "nickname", user_nickname)
            if avatar_url:
                pipe.hset(user_hash_key, "avatar_url", avatar_url)
            pipe.hincrby(user_hash_key, "total_likes", like_count)
            pipe.hincrby(user_hash_key, like_type_key, like_count)
            pipe.hincrbyfloat(user_hash_key, "points_from_likes", points)
            pipe.execute()

    def process_gift(
        self,
        user_id: str,
        user_nickname: str,
        coin_value_per_unit: int,
        gift_id: str,
        gift_name: str,
        gift_quantity: int,
        avatar_url: str = None,
    ):
        """
        ประมวลผล Gift
        """
        multiplier = self._get_gift_multiplier(coin_value_per_unit)
        points = (coin_value_per_unit * multiplier) * gift_quantity
        total_coin_value = coin_value_per_unit * gift_quantity

        # print(f"🎁 [{user_nickname}] got {points} points from {gift_quantity}x {gift_name}")

        user_key = self._get_user_key(user_id, user_nickname)
        user_summary_hash_key = f"{self.user_data_key_prefix}:{user_id}"
        user_gifts_hash_key = f"session:{self.session_id}:user_gifts:{user_id}"

        self.r.zincrby(self.leaderboard_key, points, user_key)

        pipe = self.r.pipeline()
        pipe.hset(user_summary_hash_key, "nickname", user_nickname)
        if avatar_url:
            pipe.hset(user_summary_hash_key, "avatar_url", avatar_url)
        pipe.hincrby(user_summary_hash_key, "total_gift_coins", total_coin_value)
        pipe.hincrby(user_summary_hash_key, "total_gifts_sent", gift_quantity)
        pipe.hincrbyfloat(user_summary_hash_key, "points_from_gifts", points)

        gift_field_key = f"{gift_id}|{gift_name}"
        pipe.hincrby(user_gifts_hash_key, gift_field_key, gift_quantity)
        pipe.execute()

    def process_comment(
        self,
        user_id: str,
        comment_text: str,
        user_nickname: str = "",
        avatar_url: str = None,
    ):
        """
        เก็บ Unique Comment ของ User
        """
        comment_key = f"{self.user_comments_key_prefix}:{user_id}"
        user_hash_key = f"{self.user_data_key_prefix}:{user_id}"

        # Update User Info
        if user_nickname or avatar_url:
            pipe = self.r.pipeline()
            if user_nickname:
                pipe.hset(user_hash_key, "nickname", user_nickname)
            if avatar_url:
                pipe.hset(user_hash_key, "avatar_url", avatar_url)
            pipe.execute()

        # SADD: returns 1 if new
        if self.r.sadd(comment_key, comment_text):
            # print(f"💬 Saved NEW comment for {user_id}: {comment_text}")
            self.r.hincrby(user_hash_key, "unique_comments_count", 1)

        # Always increment total comments
        # Always increment total comments
        self.r.hincrby(user_hash_key, "total_comments", 1)

    def increment_used_comments(self, user_id: str):
        """
        Increment the count of used comments for a user.
        """
        user_hash_key = f"{self.user_data_key_prefix}:{user_id}"
        self.r.hincrby(user_hash_key, "used_comments_count", 1)

    def decrement_used_comments(self, user_id: str):
        """
        Decrement the count of used comments for a user.
        """
        user_hash_key = f"{self.user_data_key_prefix}:{user_id}"
        # Ensure we don't go below 0
        current = int(self.r.hget(user_hash_key, "used_comments_count") or 0)
        if current > 0:
            self.r.hincrby(user_hash_key, "used_comments_count", -1)

    # ==================================================================
    # == ส่วนของการ "แสดงผล" (คำนวณจาก ZSET ที่เตรียมไว้แล้ว) ==
    # ==================================================================


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
        self.leaderboard_key = f"session:{self.session_id}:leaderboard"  # ZSET

        # Key สำหรับเก็บ "ข้อมูลดิบ" ของแต่ละ User (สำหรับข้อ 5)
        self.user_data_key_prefix = f"session:{self.session_id}:user_data"  # HASH

        # Key สำหรับเก็บ "Unique Comments" (สำหรับข้อ 5)
        self.user_comments_key_prefix = f"session:{self.session_id}:comments"  # SET

    def _get_gift_multiplier(self, coin_value: int) -> int:
        """
        คำนวณตัวคูณตามมูลค่า Coin (Logic ข้อ 3)
        """
        if coin_value <= 4:
            return 5
        if coin_value <= 9:
            return 6
        if coin_value <= 19:
            return 7
        if coin_value <= 49:
            return 8
        if coin_value <= 99:
            return 10
        if coin_value <= 299:
            return 15
        if coin_value <= 999:
            return 20
        return 30  # >= 1000

    def _get_user_key(self, user_id: str, user_nickname: str) -> str:
        """สร้าง Key มาตรฐานสำหรับ ZSET"""
        return f"{user_id}|{user_nickname}"

    def process_like(
        self,
        user_id: str,
        user_nickname: str,
        like_count: int,
        is_follower: bool,
        avatar_url: str = None,
    ):
        """
        ประมวลผล Like:
        1. คำนวณคะแนนเป็น float
        2. อัปเดต Leaderboard (ZSET)
        3. เก็บสถิติดิบ (HASH)
        """

        if is_follower:
            # 10 likes = 1 point
            points = like_count / 10.0
            like_type_key = "likes_as_follower"
        else:
            # 15 likes = 1 point
            points = like_count / 10.0
            like_type_key = "likes_as_non_follower"

        if points > 0:
            # print(f"❤️  [{user_nickname}] (Follower: {is_follower}) got {points:.4f} points from {like_count} likes")

            user_key = self._get_user_key(user_id, user_nickname)
            user_hash_key = f"{self.user_data_key_prefix}:{user_id}"

            # 2. อัปเดต Leaderboard (ZSET)
            self.r.zincrby(self.leaderboard_key, points, user_key)

            # 3. เก็บสถิติดิบ (HASH)
            pipe = self.r.pipeline()
            pipe.hset(user_hash_key, "nickname", user_nickname)
            if avatar_url:
                pipe.hset(user_hash_key, "avatar_url", avatar_url)
            pipe.hincrby(user_hash_key, "total_likes", like_count)
            pipe.hincrby(user_hash_key, like_type_key, like_count)
            pipe.hincrbyfloat(user_hash_key, "points_from_likes", points)
            pipe.execute()

    def process_gift(
        self,
        user_id: str,
        user_nickname: str,
        coin_value_per_unit: int,
        gift_id: str,
        gift_name: str,
        gift_quantity: int,
        avatar_url: str = None,
        gift_icon: str = None,
    ):
        """
        ประมวลผล Gift
        """
        multiplier = self._get_gift_multiplier(coin_value_per_unit)
        points = (coin_value_per_unit * multiplier) * gift_quantity
        total_coin_value = coin_value_per_unit * gift_quantity

        # print(f"🎁 [{user_nickname}] got {points} points from {gift_quantity}x {gift_name}")

        user_key = self._get_user_key(user_id, user_nickname)
        user_summary_hash_key = f"{self.user_data_key_prefix}:{user_id}"
        user_gifts_hash_key = f"session:{self.session_id}:user_gifts:{user_id}"
        gift_meta_key = f"session:{self.session_id}:gift_meta"

        self.r.zincrby(self.leaderboard_key, points, user_key)

        pipe = self.r.pipeline()
        pipe.hset(user_summary_hash_key, "nickname", user_nickname)
        if avatar_url:
            pipe.hset(user_summary_hash_key, "avatar_url", avatar_url)
        pipe.hincrby(user_summary_hash_key, "total_gift_coins", total_coin_value)
        pipe.hincrby(user_summary_hash_key, "total_gifts_sent", gift_quantity)
        pipe.hincrbyfloat(user_summary_hash_key, "points_from_gifts", points)

        # Store User Gift Count (Key = Gift ID)
        pipe.hincrby(user_gifts_hash_key, gift_id, gift_quantity)

        # Store Gift Metadata (Global for session)
        meta_data = {
            "name": gift_name,
            "diamond_count": coin_value_per_unit,
            "icon": gift_icon,
        }
        pipe.hset(gift_meta_key, gift_id, json.dumps(meta_data))

        pipe.execute()

    def process_comment(
        self,
        user_id: str,
        comment_text: str,
        user_nickname: str = "",
        avatar_url: str = None,
    ):
        """
        เก็บ Comment ของ User (JSON with Timestamp)
        """
        comment_key = f"{self.user_comments_key_prefix}:{user_id}"
        user_hash_key = f"{self.user_data_key_prefix}:{user_id}"

        # Update User Info
        if user_nickname or avatar_url:
            pipe = self.r.pipeline()
            if user_nickname:
                pipe.hset(user_hash_key, "nickname", user_nickname)
            if avatar_url:
                pipe.hset(user_hash_key, "avatar_url", avatar_url)
            pipe.execute()

        # Create Comment Object
        comment_obj = {
            "text": comment_text,
            "timestamp": datetime.now().isoformat(),
        }

        # RPUSH: Append to list (store all comments)
        self.r.rpush(comment_key, json.dumps(comment_obj))

        # Always increment total comments
        self.r.hincrby(user_hash_key, "total_comments", 1)

    def reset_user_stats(self, user_id: str):
        """
        Reset คะแนนและสถิติปัจจุบันของ User โดยย้ายไปเก็บใน 'Used' History
        """
        user_hash_key = f"{self.user_data_key_prefix}:{user_id}"
        user_gifts_hash_key = f"session:{self.session_id}:user_gifts:{user_id}"

        # 1. ดึงข้อมูลปัจจุบัน
        stats = self.r.hgetall(user_hash_key)
        current_likes = int(stats.get("total_likes", 0))
        current_gifts_sent = int(stats.get("total_gifts_sent", 0))
        current_gift_coins = int(stats.get("total_gift_coins", 0))

        # ดึง Gifts ปัจจุบัน
        current_gifts_raw = self.r.hgetall(user_gifts_hash_key)

        # 2. Atomic Update
        pipe = self.r.pipeline()

        # 2.1 เพิ่มเข้า Used Stats
        pipe.hincrby(user_hash_key, "used_likes", current_likes)
        pipe.hincrby(user_hash_key, "used_gifts_sent", current_gifts_sent)
        pipe.hincrby(user_hash_key, "used_gift_coins", current_gift_coins)
        # Reset used comments count for new session/round
        pipe.hset(user_hash_key, "used_comments_count", 0)

        # 2.2 Merge Gifts เข้า Used Gifts Breakdown (ต้องทำแบบ Read-Modify-Write ถ้าจะเก็บละเอียด)
        # แต่เพื่อความง่ายและ Atomic เราจะเก็บเป็น JSON List ของ "Sessions" หรือแค่รวมยอด
        # ในที่นี้ขอใช้วิธีเก็บแยกเป็น Key ใหม่สำหรับ Used Gifts ของ User นี้
        # used_gifts_hash_key = f"session:{self.session_id}:user_used_gifts:{user_id}"
        # for gid, count in current_gifts_raw.items():
        #     pipe.hincrby(used_gifts_hash_key, gid, int(count))

        # 2.3 Reset Current Stats
        pipe.hset(user_hash_key, "total_likes", 0)
        pipe.hset(user_hash_key, "likes_as_follower", 0)
        pipe.hset(user_hash_key, "likes_as_non_follower", 0)
        pipe.hset(user_hash_key, "points_from_likes", 0)

        pipe.hset(user_hash_key, "total_gifts_sent", 0)
        pipe.hset(user_hash_key, "total_gift_coins", 0)
        pipe.hset(user_hash_key, "points_from_gifts", 0)

        pipe.hset(user_hash_key, "total_comments", 0)
        pipe.hset(user_hash_key, "unique_comments_count", 0)

        # 2.4 Reset Gifts Breakdown
        pipe.delete(user_gifts_hash_key)

        # 2.5 Reset Score in Leaderboard
        # ต้องหา user_key ก่อน (nickname อาจเปลี่ยนได้ แต่เราจะพยายามหาจาก stats)
        nickname = stats.get("nickname", "")
        if nickname:
            user_key = self._get_user_key(user_id, nickname)
            pipe.zadd(self.leaderboard_key, {user_key: 0})

        pipe.execute()

    # ==================================================================
    # == ส่วนของการ "แสดงผล" (คำนวณจาก ZSET ที่เตรียมไว้แล้ว) ==
    # ==================================================================

    def get_leaderboard(self) -> list:
        """
        ดึง Leaderboard ทั้งหมด พร้อมรายละเอียด (Avatar, Stats, Gift Breakdown)
        """
        # Get all users (0 to -1)
        leaderboard_data = self.r.zrevrange(
            self.leaderboard_key, 0, -1, withscores=True
        )

        # Pre-fetch gift metadata
        gift_meta_key = f"session:{self.session_id}:gift_meta"
        gift_meta_raw = self.r.hgetall(gift_meta_key)
        gift_meta_map = {k: json.loads(v) for k, v in gift_meta_raw.items()}

        result = []
        for item in leaderboard_data:
            user_key = item[0]
            score = math.ceil(item[1])
            user_id, nickname = user_key.split("|", 1)

            # Fetch additional stats from Redis Hash
            user_hash_key = f"{self.user_data_key_prefix}:{user_id}"
            stats = self.r.hgetall(user_hash_key)

            # Fetch Gift Breakdown for this user
            user_gifts_hash_key = f"session:{self.session_id}:user_gifts:{user_id}"
            user_gifts_raw = self.r.hgetall(user_gifts_hash_key)

            gifts_breakdown = {}
            for gid, count in user_gifts_raw.items():
                meta = gift_meta_map.get(
                    gid, {"name": "Unknown", "diamond_count": 0, "icon": None}
                )
                gifts_breakdown[meta["name"]] = {
                    "id": gid,
                    "count": int(count),
                    "diamond_count": meta["diamond_count"],
                    "icon": meta["icon"],
                }

            result.append(
                {
                    "user_key": user_key,
                    "user_id": user_id,
                    "nickname": stats.get("nickname", nickname),
                    "score": score,
                    "avatar_url": stats.get("avatar_url", ""),
                    "score": score,
                    "avatar_url": stats.get("avatar_url", ""),
                    "comments": int(stats.get("total_comments", 0))
                    - int(stats.get("used_comments_count", 0)),
                    "likes": int(stats.get("total_likes", 0)),
                    "gifts": int(stats.get("total_gifts_sent", 0)),
                    "gifts_breakdown": gifts_breakdown,
                }
            )

        return result

    # ==================================================================
    # == ส่วนของการ "แสดงที่มา" (คำนวณจาก HASH) ==
    # ==================================================================

    def get_user_stats_and_comments(self, user_id: str) -> dict:
        """
        ดึงสถิติที่มาของคะแนน และ Comments
        """
        user_summary_hash_key = f"{self.user_data_key_prefix}:{user_id}"
        comments_key = f"{self.user_comments_key_prefix}:{user_id}"
        user_gifts_hash_key = f"session:{self.session_id}:user_gifts:{user_id}"
        gift_meta_key = f"session:{self.session_id}:gift_meta"

        # 1. ดึงสถิติดิบ (HGETALL)
        stats_raw = self.r.hgetall(user_summary_hash_key)
        stats = {k: v for k, v in stats_raw.items()}

        # 2. ดึง Comments (LRANGE) - Get all comments and parse JSON
        comments_raw = self.r.lrange(comments_key, 0, -1)
        comments = []
        for c in comments_raw:
            try:
                c_obj = json.loads(c)
                comments.append(c_obj)
            except json.JSONDecodeError:
                # Fallback for old string comments
                comments.append({"text": c, "timestamp": None})

        # 3. ดึงสถิติของขวัญ (HGETALL) & Metadata
        gifts_raw = self.r.hgetall(user_gifts_hash_key)
        gift_meta_raw = self.r.hgetall(gift_meta_key)
        gift_meta_map = {k: json.loads(v) for k, v in gift_meta_raw.items()}

        gifts_breakdown = {}
        for gid, count in gifts_raw.items():
            meta = gift_meta_map.get(
                gid, {"name": "Unknown", "diamond_count": 0, "icon": None}
            )
            gifts_breakdown[meta["name"]] = {
                "id": gid,
                "count": int(count),
                "diamond_count": meta["diamond_count"],
                "icon": meta["icon"],
            }

        return {
            "stats": stats,
            "comments": comments,
            "gifts_breakdown": gifts_breakdown,
        }
