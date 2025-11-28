# TikTok Live Support System

A comprehensive system for capturing TikTok Live events (Comments, Likes, Gifts), calculating scores, and displaying a real-time leaderboard and overlay. Ideal for interactive live streaming activities.

![Admin Dashboard](snapshot/ck6219ck6219ck62.png)

## 📋 Table of Contents

- [Key Features](#-key-features)
- [Installation](#-installation)
- [Usage](#-usage)
- [Configuration](#-configuration)
- [Key Libraries](#-key-libraries)
- [Terms of Use](#-terms-of-use)

## ✨ Key Features

- **Real-time Leaderboard**: Rank participants based on scores (Like, Gift, Comment).
- **Interactive Overlays**: Ready-to-use overlays for streaming software (OBS, vMix).
  - **Leaderboard Overlay**: Displays top 1-5 users in real-time.
  - **Question Overlay**: Displays selected comments with smooth transitions.
- **Session Management**: Save live history and resume previous sessions.
- **Admin Control**: Centralized dashboard for organizers (Reset scores, Select comments, Stop/Start stream).

## 🛠 Installation

### Backend

1. Navigate to the `backend` folder.
2. Create and activate a Virtual Environment:
   ```bash
   python -m venv venv
   # Windows
   venv\Scripts\activate
   # Mac/Linux
   source venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Ensure Redis and PostgreSQL services are running (Docker Compose recommended).

### Frontend

1. Navigate to the `frontend` folder.
2. Install dependencies:
   ```bash
   npm install
   ```

### Docker (Recommended)

Run the entire system using Docker Compose:

```bash
docker-compose up --build
```

## 🚀 Usage

Once the system is running, you can access the following interfaces:

- **Frontend (Main UI):** `http://localhost:5173`
- **Backend API Docs:** `http://localhost:8000/docs`

### 1. Admin Dashboard

URL: `http://localhost:5173/`

The main control center for the organizer:

- **Control Panel**: Start/Stop stream, Create new session, or Resume session.
- **Live Leaderboard**: Real-time ranking table.
- **User Details**: View individual player stats (Comment history, Gift Breakdown).
  - **Reset Score**: Reset individual scores (System automatically selects the next user).
  - **Select Comment**: Click the 🛜 icon to broadcast a comment to the Question Overlay.

![Admin View](snapshot/ck6219ck6219ck62.png)

### 2. Leaderboard Overlay

URL: `http://localhost:5173/overlay`

Designed for OBS with a Green Screen background for Chroma Key.

- Displays Avatar, Name, and Score for Top 5.
- Animations for rank changes.
- Crown 👑 icon for the 1st place (rotated 30 degrees).

![Leaderboard Overlay](snapshot/2gf1ai2gf1ai2gf1.png)

### 3. Question Overlay

URL: `http://localhost:5173/question`

Displays selected comments. Green Screen background.

- Shows Avatar, Name, and Comment content.
- Smooth Pop in/out transition effects when changing comments.

### 4. Session History

URL: `http://localhost:5173/sessions`

View past live sessions.

- List of all sessions (Start Time, End Time, Total Users).
- View details of each session (Participant list, Total stats).
- Resume button ▶️ to continue an old session.

![Session History](<snapshot/ck6219ck6219ck62%20(2).png>)

## ⚙️ Configuration

### Environment Variables

Create a `.env` file in the root folder:

```env
DB_USER=admin
DB_PASSWORD=password
# Add other variables as defined in docker-compose.yaml
```

### Gift Multiplier Configuration

The system applies a score multiplier based on the gift's coin value. You can modify this logic in:
`backend/app/services/scoring_service.py`

Locate the `_get_gift_multiplier` function and adjust the values:

```python
def _get_gift_multiplier(self, coin_value: int) -> int:
    if coin_value <= 4:
        return 5  # Multiplier x5
    # ... Modify conditions here
```

## 📚 Key Libraries

### Backend

- **[FastAPI](https://fastapi.tiangolo.com/)**: High-performance web framework for building APIs.
- **[TikTokLive](https://github.com/isaackogan/TikTokLive)**: Core library for connecting to and receiving events from TikTok Live.
- **[Redis](https://redis.io/)**: Used for caching and the Real-time Leaderboard (ZSET).
- **[SQLAlchemy](https://www.sqlalchemy.org/)**: ORM for database management.

### Frontend

- **[Vue.js 3](https://vuejs.org/)**: JavaScript Framework for building the UI.
- **[Vite](https://vitejs.dev/)**: Fast build tool for the frontend.
- **[TailwindCSS](https://tailwindcss.com/)**: Utility-first CSS framework for styling.
- **[Pinia](https://pinia.vuejs.org/)**: State Management for Vue.

## ⚠️ Terms of Use

1. This project is for educational and testing purposes only.
2. The developers are not affiliated with TikTok or ByteDance.
3. Usage of the `TikTokLive` library must comply with TikTok's terms of service. Users assume all risks associated with its use.
4. Do not use this tool for illegal activities or to violate the privacy of others.
