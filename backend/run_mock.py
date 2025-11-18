import asyncio
import redis
import time
from app.services.scoring_service import ScoringService
from app.adapters.mock_adapter import MockLiveAdapter

# --- Config ---
REDIS_HOST = 'localhost'
REDIS_PORT = 6379
MOCK_FILE = 'mock_data.jsonl'
SESSION_ID = f"live_test_{int(time.time())}" # สร้าง Session ID ใหม่ทุกครั้งที่รัน

async def main():
    # 1. เชื่อมต่อ Redis
    try:
        r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
        r.ping()
        print(f"✅ Connected to Redis at {REDIS_HOST}:{REDIS_PORT}")
    except Exception as e:
        print(f"❌ Could not connect to Redis: {e}")
        return

    # 2. ล้างข้อมูลเก่า (ถ้าต้องการเริ่ม Session ใหม่จริงๆ)
    print(f"🧹 Clearing old data for session: {SESSION_ID} (if any)")
    # หา Key ทั้งหมดที่เกี่ยวกับ Session นี้แล้วลบทิ้ง
    for key in r.scan_iter(f"session:{SESSION_ID}:*"):
        r.delete(key)

    # 3. สร้าง Service และ Adapter
    scoring_service = ScoringService(redis_client=r, session_id=SESSION_ID)
    mock_adapter = MockLiveAdapter(scoring_service, mock_file_path=MOCK_FILE)
    
    # 4. เริ่มจำลอง
    await mock_adapter.simulate_from_file(speed_multiplier=5.0) 
    
    # 5. สรุปผล
    print("\n========= 🏆 FINAL LEADERBOARD 🏆 =========")
    top_5 = scoring_service.get_top_5_leaderboard()
    
    if not top_5:
        print("No scores recorded.")
        return

    for i, entry in enumerate(top_5):
        print(f"#{i+1}: {entry['user_key']} - {entry['score']} points")

    # 6. [TEST] ทดสอบดึงข้อมูลดิบของที่ 1 (ข้อ 5)
    print("\n========= 📊 STATS FOR WINNER 📊 =========")
    winner_key = top_5[0]['user_key']
    winner_id, winner_name = winner_key.split('|', 1)
    
    print(f"Fetching stats for: {winner_name} ({winner_id})")
    
    winner_data = scoring_service.get_user_stats_and_comments(winner_id)
    
    print("\n--- Raw Stats (From HASH) ---")
    print(winner_data.get("stats"))
    
    print("\n--- Unique Comments (From SET) ---")
    print(winner_data.get("comments")[:5]) # แสดง 5 คอมเมนต์แรก
    
    print("\n--- Gift Breakdown (From HASH) ---")
    print(winner_data.get("gifts_breakdown"))

if __name__ == "__main__":
    asyncio.run(main())