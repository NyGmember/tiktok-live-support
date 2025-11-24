from app.models.log import SystemLog
from app.models.base import AsyncSessionLocal
import json
import traceback


class LoggingService:
    def __init__(self):
        self.log_callback = None

    def set_callback(self, callback):
        self.log_callback = callback

    async def log(self, level: str, message: str, details: dict = None):
        """
        Log system events to Database and Console
        """
        try:
            async with AsyncSessionLocal() as session:
                log_entry = SystemLog(
                    level=level,
                    message=message,
                    details=json.dumps(details, default=str) if details else None,
                )
                session.add(log_entry)
                await session.commit()
        except Exception as e:
            print(f"Failed to write log to DB: {e}")

        # Always print to console
        print(f"[{level}] {message}")

        # Trigger callback if set (e.g. for WebSocket)
        if self.log_callback:
            try:
                self.log_callback(level, message, details)
            except Exception as e:
                print(f"Error in log callback: {e}")

    async def error(self, message: str, error: Exception = None):
        details = {}
        if error:
            details["error"] = str(error)
            details["traceback"] = traceback.format_exc()
        await self.log("ERROR", message, details)

    async def info(self, message: str, details: dict = None):
        await self.log("INFO", message, details)

    async def warning(self, message: str, details: dict = None):
        await self.log("WARNING", message, details)
