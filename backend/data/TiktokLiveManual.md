# รายการ Attributes ของ TikTokLive Events

เอกสารนี้สรุป Attribute ที่สำคัญของ Event object ต่างๆ ที่ได้รับจากไลบรารี `TikTok-Live-Python` เพื่อใช้ในการอ้างอิงและพัฒนาโปรเจกต์

## Object พื้นฐาน

Object เหล่านี้มักจะเป็นส่วนประกอบย่อยอยู่ภายใน Event หลักๆ

### User

ข้อมูลเกี่ยวกับผู้ใช้งาน TikTok

| Attribute | Type | คำอธิบาย |
| :--- | :--- | :--- |
| `unique_id` | str | ID ที่ใช้แสดงบนโปรไฟล์ (เช่น @nakarin2547n) |
| `nickname` | str | ชื่อที่แสดงบนโปรไฟล์ |
| `user_id` | int | ID เฉพาะตัวของผู้ใช้ |
| `profile_picture_url` | str | URL ของรูปโปรไฟล์ |
| `follow_role` | int | สถานะการติดตาม (เช่น 0: ไม่ได้ติดตาม, 1: เพื่อน, 2: กำลังติดตาม) |
| `is_moderator` | bool | เป็น Moderator หรือไม่ |
| `is_subscriber` | bool | เป็น Subscriber หรือไม่ |

### Gift

ข้อมูลเกี่ยวกับของขวัญ

| Attribute | Type | คำอธิบาย |
| :--- | :--- | :--- |
| `id` | int | ID ของของขวัญ |
| `name` | str | ชื่อของขวัญ |
| `info.diamond_count` | int | จำนวนเพชรที่ใช้ |
| `type` | int | ประเภทของขวัญ (เช่น 1: ของขวัญปกติ) |
| `streakable` | bool | สามารถส่งแบบต่อเนื่อง (Combo) ได้หรือไม่ |
| `image_url` | str | URL รูปภาพของขวัญ |

---

## Main Events

Event หลักที่เกิดขึ้นระหว่างการ Live

### ConnectEvent

เกิดขึ้นเมื่อ Client เชื่อมต่อกับ Live สำเร็จ

| Attribute | Type | คำอธิบาย |
| :--- | :--- | :--- |
| `client` | TikTokLiveClient | Instance ของ Client ที่เชื่อมต่อ |

### DisconnectEvent

เกิดขึ้นเมื่อ Client หลุดจากการเชื่อมต่อ

| Attribute | Type | คำอธิบาย |
| :--- | :--- | :--- |
| `client` | TikTokLiveClient | Instance ของ Client ที่หลุดการเชื่อมต่อ |

### CommentEvent

เกิดขึ้นเมื่อมีคนคอมเมนต์ใน Live

| Attribute | Type | คำอธิบาย |
| :--- | :--- | :--- |
| `user` | `User` | Object ของผู้ที่ส่งคอมเมนต์ |
| `comment` | str | ข้อความคอมเมนต์ |
| `msg_id` | int | ID ของข้อความ |
| `common` | object | ข้อมูล chung ของ event |

**ตัวอย่างการใช้งาน:**
```python
print(f"[{event.user.nickname}]: {event.comment}")
```

### LikeEvent

เกิดขึ้นเมื่อมีคนกดหัวใจใน Live

| Attribute | Type | คำอธิบาย |
| :--- | :--- | :--- |
| `user` | `User` | Object ของผู้ที่กดหัวใจ |
| `count` | int | จำนวนหัวใจที่ส่งมาใน Event นี้ (มักจะมาเป็นชุด) |
| `total_likes` | int | จำนวนหัวใจรวมทั้งหมดของ Live ณ เวลานั้น |
| `common` | object | ข้อมูล chung ของ event |

**ตัวอย่างการใช้งาน:**
```python
print(f"[{event.user.nickname}] sent {event.count} likes!")
```

### GiftEvent

เกิดขึ้นเมื่อมีคนส่งของขวัญ

| Attribute | Type | คำอธิบาย |
| :--- | :--- | :--- |
| `user` | `User` | Object ของผู้ที่ส่งของขวัญ |
| `gift` | `Gift` | Object ของขวัญที่ถูกส่ง |
| `streaking` | bool | `True` ถ้ากำลังอยู่ในช่วง Combo (Streak) |
| `repeat_count` | int | จำนวนครั้งที่ส่งของขวัญชิ้นนี้ใน Streak ปัจจุบัน |
| `repeat_end` | int | `1` ถ้าเป็นของขวัญชิ้นสุดท้ายใน Streak |
| `common` | object | ข้อมูล chung ของ event |

**ตัวอย่างการใช้งาน:**
```python
# ของขวัญที่ส่งครั้งเดียว หรือเป็นชิ้นแรกของ Combo
if event.gift.streakable and not event.streaking:
    print(f"[{event.user.nickname}] started a streak of {event.gift.name}!")

# ของขวัญที่ไม่สามารถ Combo ได้
elif not event.gift.streakable:
    print(f"[{event.user.nickname}] sent a {event.gift.name}!")
```

### JoinEvent

เกิดขึ้นเมื่อมีคนเข้าร่วม Live

| Attribute | Type | คำöธิบาย |
| :--- | :--- | :--- |
| `user` | `User` | Object ของผู้ที่เข้าร่วม |

### FollowEvent

เกิดขึ้นเมื่อมีคนกดติดตาม Host ระหว่าง Live

| Attribute | Type | คำอธิบาย |
| :--- | :--- | :--- |
| `user` | `User` | Object ของผู้ที่กดติดตาม (ข้อมูลสำคัญ) |
| `common` | object | ข้อมูล chung ของ event (อาจทำให้เกิด Error ตอน `to_dict()`) |

**ตัวอย่างการใช้งาน (แนะนำ):**
```python
# หลีกเลี่ยงการใช้ event.to_dict() ทั้งหมด
# ให้ดึงข้อมูลจาก user object โดยตรง
user_data = event.user.to_dict()
print(f"[{user_data['nickname']}] followed the host!")
```

### ShareEvent

เกิดขึ้นเมื่อมีคนแชร์ Live

| Attribute | Type | คำอธิบาย |
| :--- | :--- | :--- |
| `user` | `User` | Object ของผู้ที่แชร์ (ข้อมูลสำคัญ) |
| `common` | object | ข้อมูล chung ของ event (อาจทำให้เกิด Error ตอน `to_dict()`) |

**ตัวอย่างการใช้งาน (แนะนำ):**
```python
# หลีกเลี่ยงการใช้ event.to_dict() ทั้งหมด
# ให้ดึงข้อมูลจาก user object โดยตรง
user_data = event.user.to_dict()
print(f"[{user_data['nickname']}] shared the stream!")
```
