import asyncio
import json
import time
import betterproto
from TikTokLive import TikTokLiveClient
from TikTokLive.client.logger import LogLevel, TikTokLiveLogHandler
from TikTokLive.events import CommentEvent, GiftEvent, LikeEvent, ConnectEvent, DisconnectEvent, ShareEvent, FollowEvent

# ================= CONFIGURATION =================
# ใส่ชื่อ TikTok ID ของคนที่เราต้องการไปดูดข้อมูล (ควรเลือกห้องที่มีคนดูและ Activity เยอะหน่อย เพื่อ Test Load)
TARGET_TIKTOK_ID = "@juneang2004" 
OUTPUT_FILE = "mock_data_1.jsonl"

# For debugging
show_error_event = False

def save_event_to_file(event_type: str, event_data: dict):
    """บันทึก Event ลงไฟล์ JSONL"""
    
    # สร้างโครงสร้างข้อมูลที่จะบันทึก
    record = {
        "timestamp": time.time(),
        "type": event_type,
        "payload": event_data
    }
    
    # เปิดไฟล์แบบ Append ('a') เพื่อเขียนต่อท้ายไปเรื่อยๆ
    with open(OUTPUT_FILE, "a", encoding="utf-8") as f:
        # ensure_ascii=False เพื่อให้เก็บภาษาไทยได้ถูกต้อง
        f.write(json.dumps(record, ensure_ascii=False) + "\n")

def remove_attr(event):
    if hasattr(event, 'public_area_message_common'):
        delattr(event, 'public_area_message_common')
    return event


# ================= SETUP CLIENT =================
client: TikTokLiveClient = TikTokLiveClient(
    unique_id=TARGET_TIKTOK_ID
)

# ================= EVENT HANDLERS =================

async def check_on_live():
    # Run 24/7
    while True:

        # Check if they're live
        while not await client.is_live():
            client.logger.info("Client is currently not live. Checking again in 60 seconds.")
            await asyncio.sleep(60)  # Spamming the endpoint will get you blocked

        # Connect once they become live
        # client.logger.info("Requested client is live!")
        await client.connect()

@client.on(ConnectEvent)
async def on_connect(_: ConnectEvent):
    client.logger.info(f"✅ Connected to {TARGET_TIKTOK_ID}")
    client.logger.info(f"🔴 Recording events to {OUTPUT_FILE}...")

@client.on(DisconnectEvent)
async def on_disconnect(_: DisconnectEvent):
    client.logger.info("❌ Disconnected")

@client.on(CommentEvent)
async def on_comment(event: CommentEvent):
    try: 
        # Remove the problematic attribute before serialization
        event = remove_attr(event)

        # แปลง Object เป็น Dict เพื่อให้ Save เป็น JSON ได้
        data = event.to_dict()       
        save_event_to_file("comment", data)
        
        client.logger.info(f"💬 [{event.user.nickname}]: {event.comment}")
    except Exception as e:
        client.logger.error(f"commentEvent error: {e}")


@client.on(LikeEvent)
async def on_like(event: LikeEvent):
    try:
        # Remove the problematic attribute before serialization
        event = remove_attr(event)

        data = event.to_dict()         
        save_event_to_file("like", data)
        
        # Like มักจะมาเป็น Batch เช่น "user sent 15 likes"
        client.logger.info(f"❤️ [{event.user.unique_id}] sent {event.count} likes")
    except Exception as e:
        client.logger.error(f"likeEvent error: {e}")
    
@client.on(GiftEvent)
async def on_gift(event: GiftEvent):
    try:
        # Remove the problematic attribute before serialization
        event = remove_attr(event)

        if event.gift.streakable and not event.streaking:
            data = event.to_dict()
            client.logger.info(f"🎁 [{event.user.unique_id}] sent sent {event.repeat_count}x \"{event.gift.name}\"")
            save_event_to_file("gift", data)
        # Non-streakable gift
        elif not event.gift.streakable:
            data = event.to_dict()
            client.logger.info(f"🎁 [{event.user.unique_id}] sent {event.gift.name}")
            save_event_to_file("gift", data)
    except Exception as e:
        client.logger.error(f"giftEvent error: {e}")
    
@client.on(FollowEvent)
async def on_follow(event: FollowEvent):
    try:
        # Avoid event.to_dict() due to internal errors with CommonMessageData
        # Manually create the payload from the essential 'user' object.
        data = event.user.to_dict()
        
        save_event_to_file("follow", data)
        
        client.logger.info(f"🏃‍♂️ [{event.user.unique_id}] followed the host")
    except Exception as e:
        client.logger.error(f"followEvent error: {e}")


@client.on(ShareEvent)
async def on_share(event: ShareEvent):
    try:
        # Avoid event.to_dict() due to internal errors with CommonMessageData
        # Manually create the payload from the essential 'user' object.
        data = event.user.to_dict()
        
        save_event_to_file("share", data)
        
        client.logger.info(f"🔗 [{event.user.unique_id}] shared the stream")
    except Exception as e:
        client.logger.error(f"shareEvent error: {e}")

# ================= MAIN LOOP =================
if __name__ == '__main__':
    # ลบไฟล์เก่าทิ้งก่อนเริ่ม (ถ้าต้องการ)
    # import os
    # if os.path.exists(OUTPUT_FILE):
    #     os.remove(OUTPUT_FILE)
        
    try:
        client.logger.setLevel(LogLevel.INFO.value)
        asyncio.run(check_on_live())
    except Exception as e:
        client.logger.error(f"Error: {e}")