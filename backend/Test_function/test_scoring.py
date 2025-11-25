import sys
import os
import redis
import json
import asyncio

# Add backend directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.services.scoring_service import ScoringService


def test_scoring():
    print("Connecting to Redis...")
    try:
        r = redis.Redis(host="localhost", port=6379, decode_responses=True)
        r.ping()
        print("✅ Redis connected")
    except Exception as e:
        print(f"❌ Redis connection failed: {e}")
        return

    session_id = "test_verification_session"
    # Clear previous test data
    keys = r.keys(f"session:{session_id}:*")
    if keys:
        r.delete(*keys)

    service = ScoringService(r, session_id)
    user_id = "user_123"
    nickname = "TestUser"
    avatar = "http://avatar.url"

    print("\n--- Testing Process Gift ---")
    service.process_gift(
        user_id=user_id,
        user_nickname=nickname,
        coin_value_per_unit=10,
        gift_id="gift_1",
        gift_name="Rose",
        gift_quantity=5,
        avatar_url=avatar,
        gift_icon="http://gift.icon/rose.png",
    )
    print("✅ Gift processed")

    print("\n--- Testing Process Comment ---")
    service.process_comment(user_id, "Hello World", nickname, avatar)
    service.process_comment(user_id, "Second Comment", nickname, avatar)
    print("✅ Comments processed")

    print("\n--- Testing Get Leaderboard ---")
    leaderboard = service.get_leaderboard()
    print(f"Leaderboard: {json.dumps(leaderboard, indent=2)}")

    user_entry = leaderboard[0]
    if "gifts_breakdown" in user_entry and "Rose" in user_entry["gifts_breakdown"]:
        print("✅ Gift Breakdown present in Leaderboard")
        rose_data = user_entry["gifts_breakdown"]["Rose"]
        if rose_data["icon"] == "http://gift.icon/rose.png":
            print("✅ Gift Icon correct")
        else:
            print("❌ Gift Icon mismatch")
    else:
        print("❌ Gift Breakdown missing or incorrect")

    print("\n--- Testing Get User Stats ---")
    stats = service.get_user_stats_and_comments(user_id)
    print(f"User Stats: {json.dumps(stats, indent=2)}")

    comments = stats["comments"]
    if len(comments) == 2:
        print("✅ Correct number of comments")
        if "timestamp" in comments[0] and comments[0]["text"] == "Hello World":
            print("✅ Comment 1 structure correct")
        else:
            print("❌ Comment 1 structure incorrect")
    else:
        print(f"❌ Expected 2 comments, got {len(comments)}")


if __name__ == "__main__":
    test_scoring()
