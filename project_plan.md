# Tiktok Live Support

## 🏗️ System Architecture Overview

ระบบนี้ทำงานในรูปแบบ **Event-Driven Architecture** โดยมีหัวใจสำคัญคือ **Backend Server** ที่เราจะเขียนด้วย Python เพื่อจัดการ Logic คะแนนและ State ของเกมทั้งหมด

### องค์ประกอบหลัก (The Stack)

1.  **Data Ingestion (Listener):** ตัวรับข้อมูลจาก TikTok Live
2.  **Processing Core (Backend):** คำนวณคะแนน, จัดการคิว, และ API
3.  **State Management (Database):** เก็บข้อมูล User, Score, Session
4.  **Real-time Gateway:** ส่งข้อมูลไปยังหน้าจอ Live (OBS) และหน้าจอ Admin
5.  **Frontend (Overlay & Admin):** หน้าจอแสดงผล

-----

## 🛠️ เครื่องมือและเทคโนโลยี (Tools Selection)

### 1\. Data Ingestion: `TikTokLive` (Python Library)

  * `TikTokLive` (Python Library by isaackogan)**
      * **เหตุผล:** คุณเป็น Python Pro ไลบรารีนี้ Wrapper ตัว Web Socket ของ TikTok Webcast ได้โดยตรง
      * **ข้อดี:** ได้ Data แบบ Real-time (ms), เช็คสถานะ `is_following` ได้แม่นยำกว่า, ดักจับ Gift Combo ได้ละเอียด
      * **ความเหมาะสม:** เหมาะมากกับข้อ 3 ที่มีการคิดคะแนนซับซ้อน

### 2\. Backend Framework: `FastAPI`

  * ต้องใช้ **Asynchronous** เต็มรูปแบบเพราะ Events จะเข้ามามหาศาล (Comments + Likes รัวๆ)
  * FastAPI เร็วกว่า Flask/Django และรองรับ WebSocket ได้ดีเยี่ยม

### 3\. Database & Caching: `Redis` + `SQLite/PostgreSQL`

  * **Redis (สำคัญมาก):** ใช้ฟีเจอร์ **Sorted Sets (ZSET)** เพื่อทำ Real-time Leaderboard การ query top 5 จาก Redis ใช้เวลาน้อยกว่า SQL มาก และรองรับการ update คะแนนถี่ๆ
  * **SQLite/PostgreSQL:** ใช้เก็บ History คำถาม, Comments, และ Session Data

### 4\. Frontend: `Vue.js` หรือ `React` (SPA)

  * แสดงผลบน OBS ผ่าน Browser Source
  * Animation การสลับลำดับ (Flip animations) ทำในนี้ง่ายกว่า

-----

## 📝 แผนการทำงานและ Technical Breakdown (Step-by-Step)

### Phase 1: Data Ingestion & Scoring Engine (Python)

  * **Like Handling:** TikTok ส่ง Likes มาเป็น Batch (เช่น user A กด 50 ที มันอาจส่ง event มาแค่ 1-2 ครั้ง พร้อม count)
      * *Logic:* เราต้องเขียน Buffer เพื่อสะสมจำนวน Like แล้วหารด้วย 10 (Follower) หรือ 15 (Non-follower) เพื่อแปลงเป็นคะแนน
  * **Gift Handling:** ต้องระวังเรื่อง "Combo" ถ้า User กดส่งกุหลาบ 10 ดอกรัวๆ API อาจส่งแยก หรือส่งรวม เราต้อง Handle `gift_type` และ `diamond_count` เข้ากับตาราง Multiplier ของคุณ

### Phase 2: Real-time Leaderboard (Redis ZSET)

  * ใช้ Redis ZSET: `ZINCRBY leaderboard:session_id score user_id`
  * เมื่อคะแนนเปลี่ยน ส่ง WebSocket message ไปที่ Frontend ทันที
  * **Animation:** ส่งข้อมูลไปบอก Frontend ว่า "User A แซง User B" เพื่อให้ Frontend เล่นท่า Animation (ข้อ 4)

### Phase 3: Admin Control (Host Panel)

Host ต้องการหน้าจอควบคุม (Tablet หรือ จอแยก) โดยมีปุ่ม:

  * **Select Winner:** Backend ดึง Top 1 จาก Redis -\> Query database หา Comment ล่าสุด หรือ สุ่ม Comment ของ User นั้น -\> ส่ง JSON กลับมาแสดง -\> ลบ User ออกจาก Redis ZSET (ข้อ 5)
  * **Freeze/Stop:** Backend รับ Trigger -\> ส่ง Countdown Event ไป Frontend (5s) -\> Set flag `is_accepting_answers = False` -\> Backend หยุด process events ใหม่ (ข้อ 7)

### Phase 4: Session Management

  * **New/Continue:** สร้าง `session_id`
      * *Start New:* สร้าง Redis Key ใหม่
      * *Continue:* โหลดข้อมูลจาก SQL กลับเข้า Redis หรือใช้ Redis Key เดิมถ้ายังไม่ expire

-----

## 💡 คำแนะนำเพิ่มเติมในฐานะที่ปรึกษา (Pro Tips)

1.  **การแสดง Comment (ข้อ 5-6):**

      * ผู้ใช้อาจจะ Spam comment เดิมๆ เพื่อดันข้อความ ระบบควรเก็บ Comment ล่าสุด หรือ Unique Comment ของ User นั้นๆ ลงใน Redis Hash `user:comments:{id}` เพื่อให้ตอน Host กดเลือกผู้ชนะ ระบบจะดึง Comment ทั้งหมดมาให้เลือกได้ทันทีโดยไม่ต้องไปไล่หาใน Log

2.  **OBS Integration:**

      * สร้างหน้าเว็บ 2 หน้า: `/overlay` (พื้นหลังใส สำหรับ OBS) และ `/admin` (สำหรับ Host)
      * ใช้ **OBS WebSocket** (Optional) ถ้าต้องการให้ปุ่มใน Admin Panel ไปสั่งเปลี่ยน Scene ใน OBS ได้ด้วย (เช่น ตอน Countdown จบ ให้ตัดภาพไปที่หน้า Host)

3.  **Rate Limiting & Safety:**

      * ระวัง TikTok แบน IP หาก connect บ่อยเกินไป ถ้า self-host แนะนำให้ใช้ Proxy แต่ถ้าใช้ไลบรารี Python ปกติรันเครื่องเดียวมักไม่มีปัญหา

## สรุป Flow การทำงานของโค้ด (Python Example Concept)

```python
# Concept Code (Pseudo)
from TikTokLive import TikTokLiveClient
from TikTokLive.types.events import LikeEvent, GiftEvent
import redis

client = TikTokLiveClient(unique_id="@target_user")
r = redis.Redis()

@client.on("like")
async def on_like(event: LikeEvent):
    if not is_accepting_answers: return
    
    is_follower = event.user.is_follower # เช็คสถานะ
    points = calculate_like_points(event.count, is_follower) 
    
    # Update Redis
    r.zincrby("current_leaderboard", points, event.user.unique_id)
    # Broadcast update via Websocket to OBS

@client.on("gift")
async def on_gift(event: GiftEvent):
    if not is_accepting_answers: return
    
    multiplier = get_multiplier(event.gift.diamond_count)
    points = event.gift.diamond_count * multiplier
    
    r.zincrby("current_leaderboard", points, event.user.unique_id)
```

## Project structure
```
tiktok-live-support/
├── backend/                # FastAPI App
│   ├── app/
│   │   ├── adapters/       # TikTokLive & Mock Adapter
│   │   ├── models/         # DB Models
│   │   ├── services/       # Scoring Logic
│   │   └── main.py
│   ├── requirements.txt
│   └── .env
├── frontend/               # Vue.js App
│   ├── src/
│   └── package.json
├── docker-compose.yml      # Infrastructure Setup
└── .gitignore
```

## **📋 Database Schema Design (Concept)**

### **"เก็บ Unique Comment"** และ **"Scoring"**
1. **Users Table:** `user_id (PK, TikTok ID)`, `username`, `display_name`, `profile_pic`, `is_follower`  
2. **Sessions Table:** `session_id (PK)`, `start_time`, `end_time`, `is_active`  
3. **Scores Table:** `user_id`, `session_id`, `score`, `heart_count`, `gift_value`  
4. **Comments Table:** (สำหรับการเลือกคำถาม)  
   * `id`  
   * `session_id`  
   * `user_id`  
   * `content` (ข้อความคำถาม)  
   * `timestamp`  
