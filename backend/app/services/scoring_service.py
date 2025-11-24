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
        self.r.hincrby(user_hash_key, "total_comments", 1)

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

        # RPUSH: Append to list (store all comments)
        self.r.rpush(comment_key, comment_text)
        # print(f"💬 Saved comment for {user_id}: {comment_text}")

        # Always increment total comments
        self.r.hincrby(user_hash_key, "total_comments", 1)

    # ==================================================================
    # == ส่วนของการ "แสดงผล" (คำนวณจาก ZSET ที่เตรียมไว้แล้ว) ==
    # ==================================================================

    def get_top_5_leaderboard(self) -> list:
        """
        ดึง Top 5 Leaderboard พร้อมรายละเอียด (Avatar, Stats)
        """
        top_5 = self.r.zrevrange(self.leaderboard_key, 0, 4, withscores=True)

        result = []
        for item in top_5:
            user_key = item[0]
            score = int(item[1])
            user_id, nickname = user_key.split("|", 1)

            # Fetch additional stats from Redis Hash
            user_hash_key = f"{self.user_data_key_prefix}:{user_id}"
            stats = self.r.hgetall(user_hash_key)

            result.append(
                {
                    "user_key": user_key,
                    "user_id": user_id,
                    "nickname": stats.get("nickname", nickname),
                    "score": score,
                    "avatar_url": stats.get("avatar_url", ""),
                    "comments": int(stats.get("total_comments", 0)),
                    "likes": int(stats.get("total_likes", 0)),
                    "gifts": int(stats.get("total_gifts_sent", 0)),
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

        # 1. ดึงสถิติดิบ (HGETALL)
        stats_raw = self.r.hgetall(user_summary_hash_key)
        stats = {k: v for k, v in stats_raw.items()}

        # 2. ดึง Comments (LRANGE) - Get all comments
        comments_raw = self.r.lrange(comments_key, 0, -1)
        comments = [c for c in comments_raw]

        # 3. ดึงสถิติของขวัญ (HGETALL)
        gifts_raw = self.r.hgetall(user_gifts_hash_key)
        gifts_breakdown = {}
        for k, v in gifts_raw.items():
            key_parts = k.split("|", 1)
            gift_id = key_parts[0]
            gift_name = key_parts[1] if len(key_parts) > 1 else "Unknown Gift"

            gifts_breakdown[gift_name] = {"id": gift_id, "count": int(v)}

        return {
            "stats": stats,
            "comments": comments,
            "gifts_breakdown": gifts_breakdown,
        }
