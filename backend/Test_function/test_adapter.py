import asyncio
import sys
import os
import logging
from datetime import datetime

# Add backend directory to sys.path to allow imports from app
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.adapters.tiktok_adapter import TikTokLiveAdapter

# Configure logging to output to terminal
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class MockLoggingService:
    async def info(self, message: str, details: dict = None):
        # logger.info(f"[MockLogging] INFO: {message} | Details: {details}")
        pass

    async def error(self, message: str, error: Exception = None):
        logger.error(f"[MockLogging] ERROR: {message} | Error: {error}")

    async def warning(self, message: str, details: dict = None):
        logger.warning(f"[MockLogging] WARNING: {message} | Details: {details}")


class MockDataService:
    async def upsert_user(self, tiktok_id: str, nickname: str, avatar_url: str = None):
        # logger.info(
        #     f"[MockData] upsert_user: id={tiktok_id}, nick={nickname}, avatar={avatar_url}"
        # )
        pass

    async def upsert_gift(
        self, gift_id: str, name: str, diamond_count: int, image_url: str = None
    ):
        logger.info(
            f"[Gift-Data] upsert_gift: id={gift_id}, name={name}, diamonds={diamond_count}, img={image_url[-8:]}"
        )

    async def save_comment(self, user_id: str, session_id: str, content: str):
        # logger.info(
        #     f"[MockData] save_comment: user={user_id}, session={session_id}, content={content}"
        # )
        pass


class MockScoringService:
    def process_like(self, unique_id, nickname, count, is_follower, avatar_url=None):
        logger.info(
            f"[Like] | user={unique_id} | count={count} | is_follower={is_follower} | avatar={avatar_url[-8:]}"
        )

    def process_gift(
        self,
        unique_id,
        nickname,
        diamond_count,
        gift_id,
        gift_name,
        repeat_count,
        avatar_url=None,
        gift_icon=None,
    ):
        logger.info(
            f"[Gift] | user={unique_id} | gift={gift_name} x {repeat_count} | diamonds={diamond_count} | avatar={avatar_url[-8:]} | icon={gift_icon}"
        )

    def process_comment(self, unique_id, comment, user_nickname=None, avatar_url=None):
        logger.info(
            f"[Comment] | user={unique_id} | comment={comment} | avatar={avatar_url[-8:]}"
        )


async def main():
    unique_id = "@rokungx"
    if not unique_id:
        print("Username is required.")
        return

    print(f"Starting adapter for {unique_id}...")

    # Initialize mocks
    mock_logging = MockLoggingService()
    mock_data = MockDataService()
    mock_scoring = MockScoringService()
    session_id = "test_session_123"

    # Initialize Adapter
    adapter = TikTokLiveAdapter(
        scoring_service=mock_scoring,
        logging_service=mock_logging,
        data_service=mock_data,
        unique_id=unique_id,
        session_id=session_id,
    )

    # Start Adapter
    try:
        await adapter.start()
    except KeyboardInterrupt:
        print("\nStopping adapter...")
        await adapter.stop()
    except Exception as e:
        print(f"Error: {e}")
        await adapter.stop()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
