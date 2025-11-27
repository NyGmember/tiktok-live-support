# TikTok Live Support System

A system for capturing TikTok Live events (Comments, Likes, Gifts), calculating scores, and displaying a real-time leaderboard and overlay.

## 📋 Table of Contents

- [Installation](#-installation)
- [Usage](#-usage)
- [Configuration](#-configuration)
- [Key Libraries](#-key-libraries)
- [Terms of Use](#-terms-of-use)

## 🛠 Installation

```bash
pip install -r requirements.txt
```

4. Ensure Redis and PostgreSQL services are running.

**Frontend:**

1. Navigate to the `frontend` folder.
2. Install dependencies:
   ```bash
   npm install
   ```

## 🚀 Usage

Once the system is running, you can access the following:

- **Frontend (UI):** `http://localhost:5173`
- **Backend API Docs:** `http://localhost:8000/docs`
- **PGAdmin (Database Management):** `http://localhost:5050`
- **Redis Commander (Redis GUI):** `http://localhost:8081`

### Starting Live Capture

The backend service connects to TikTok Live. You need to specify the `unique_id` of the target Live room via the API or configuration (depending on the implementation in `capture_live.py` or API endpoint).

## ⚙️ Configuration

### Environment Variables

Create a `.env` file in the root folder with the following:

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
3. Usage of the `TikTokLive` library must comply with TikTok's terms of service. Users assume all risks associated with its use (e.g., potential access restrictions for abnormal usage).
4. Do not use this tool for illegal activities or to violate the privacy of others.
