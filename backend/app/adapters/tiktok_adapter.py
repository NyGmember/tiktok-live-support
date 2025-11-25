import asyncio
from TikTokLive import TikTokLiveClient
from TikTokLive.events import (
    CommentEvent,
    GiftEvent,
    LikeEvent,
    ConnectEvent,
    DisconnectEvent,
    ShareEvent,
    FollowEvent,
)
from app.services.scoring_service import ScoringService
from app.services.logging_service import LoggingService
from app.services.data_service import DataService
import json
from datetime import datetime


class TikTokLiveAdapter:
    def __init__(
        self,
        scoring_service: ScoringService,
        logging_service: LoggingService,
        data_service: DataService,
        unique_id: str,
        session_id: str,
    ):
        self.scoring_service = scoring_service
        self.logging_service = logging_service
        self.data_service = data_service
        self.unique_id = unique_id
        self.session_id = session_id
        self.client = TikTokLiveClient(unique_id=self.unique_id)
        self.is_running = False

        # Register events
        self.client.add_listener(ConnectEvent, self.on_connect)
        self.client.add_listener(DisconnectEvent, self.on_disconnect)
        self.client.add_listener(LikeEvent, self.on_like)
        self.client.add_listener(GiftEvent, self.on_gift)
        self.client.add_listener(CommentEvent, self.on_comment)
        self.client.add_listener(FollowEvent, self.on_follow)
        self.client.add_listener(ShareEvent, self.on_share)

    async def log_ingestion_error(self, error: Exception, event_data: dict):
        """Log ingestion errors to a JSONL file"""
        try:
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "error": str(error),
                "event_data": str(
                    event_data
                ),  # Convert to string to avoid serialization issues
            }
            with open("ingestion_errors.jsonl", "a", encoding="utf-8") as f:
                f.write(json.dumps(log_entry) + "\n")
        except Exception as log_err:
            print(f"Failed to log ingestion error: {log_err}")

    async def start(self):
        self.is_running = True
        await self.logging_service.info(
            f"Starting TikTokLiveAdapter for {self.unique_id}"
        )

        # Loop to keep checking if live
        while self.is_running:
            try:
                if not await self.client.is_live():
                    await self.logging_service.info(
                        f"{self.unique_id} is offline. Retrying in 30s..."
                    )
                    await asyncio.sleep(30)
                    continue

                await self.logging_service.info(f"Connecting to {self.unique_id}...")
                await self.client.connect()
            except Exception as e:
                await self.logging_service.error(f"Connection error: {e}", e)
                await asyncio.sleep(10)

    async def stop(self):
        self.is_running = False
        if self.client.connected:
            await self.client.disconnect()
        await self.logging_service.info("TikTokLiveAdapter stopped")

    async def on_connect(self, event: ConnectEvent):
        await self.logging_service.info(f"✅ Connected to {self.unique_id}")

    async def on_disconnect(self, event: DisconnectEvent):
        await self.logging_service.warning("❌ Disconnected from TikTok Live")

    async def on_like(self, event: LikeEvent):
        try:
            # CRITICAL: Do not access event.user directly, it raises TypeError in this version.
            # Use event.user_info or event.sender if available.
            user = getattr(event, "user_info", getattr(event, "user", None))
            if not user:
                # Fallback for some versions
                user = getattr(event, "sender", None)

            if not user:
                await self.logging_service.warning(
                    "LikeEvent received without user info"
                )
                return

            # Robust Attribute Access
            # unique_id is often 'username' in ExtendedUser
            unique_id = getattr(user, "unique_id", getattr(user, "username", None))
            # nickname is often 'nick_name' in ExtendedUser
            nickname = getattr(user, "nickname", getattr(user, "nick_name", None))

            if not unique_id or not nickname:
                await self.logging_service.warning(
                    f"Incomplete user info in LikeEvent: {unique_id}, {nickname}"
                )
                return

            # Avatar Extraction
            avatar_thumb = getattr(user, "avatar_thumb", None)
            avatar_url = None
            if avatar_thumb:
                if hasattr(avatar_thumb, "m_urls") and avatar_thumb.m_urls:
                    avatar_url = avatar_thumb.m_urls[0]
                elif hasattr(avatar_thumb, "url_list") and avatar_thumb.url_list:
                    avatar_url = avatar_thumb.url_list[0]
                elif hasattr(avatar_thumb, "urls") and avatar_thumb.urls:
                    avatar_url = avatar_thumb.urls[0]

            await self.data_service.upsert_user(unique_id, nickname, avatar_url)

            # Follower Status
            is_follower = False
            follow_info = getattr(user, "follow_info", None)
            if follow_info and hasattr(follow_info, "follow_status"):
                is_follower = follow_info.follow_status == 1

            self.scoring_service.process_like(
                unique_id,
                nickname,
                event.count,
                is_follower,
                avatar_url=avatar_url,
            )

            # Log for Admin Dashboard
            await self.logging_service.info(
                f"{nickname} sent {event.count} likes",
                details={"type": "Like"},
            )
        except Exception as e:
            # Do NOT access event.user in error handling either
            await self.log_ingestion_error(e, {"type": "Like", "data": str(event)})
            asyncio.create_task(
                self.logging_service.error(f"Error processing like: {e}", e)
            )

    async def on_gift(self, event: GiftEvent):
        try:
            # Robust User Extraction
            user = getattr(
                event,
                "user",
                getattr(event, "user_info", getattr(event, "sender", None)),
            )

            if not user:
                await self.logging_service.warning(
                    "GiftEvent received without user info"
                )
                return

            unique_id = getattr(user, "unique_id", getattr(user, "username", None))
            nickname = getattr(user, "nickname", getattr(user, "nick_name", None))

            if not unique_id or not nickname:
                await self.logging_service.warning(
                    f"Incomplete user info in GiftEvent: {unique_id}, {nickname}"
                )
                return

            # Persist User & Gift
            avatar_thumb = getattr(user, "avatar_thumb", None)
            avatar_url = None
            if avatar_thumb:
                if hasattr(avatar_thumb, "m_urls") and avatar_thumb.m_urls:
                    avatar_url = avatar_thumb.m_urls[0]
                elif hasattr(avatar_thumb, "url_list") and avatar_thumb.url_list:
                    avatar_url = avatar_thumb.url_list[0]
                elif hasattr(avatar_thumb, "urls") and avatar_thumb.urls:
                    avatar_url = avatar_thumb.urls[0]

            await self.data_service.upsert_user(unique_id, nickname, avatar_url)

            gift_icon = event.gift.icon
            gift_image = gift_icon.m_urls[0]
            # if hasattr(gift_icon, "urls") and gift_icon.urls:
            #     gift_image = gift_icon.urls[0]

            await self.data_service.upsert_gift(
                str(event.gift.id),
                event.gift.name,
                event.gift.diamond_count,
                gift_image,
            )

            if event.gift.streakable and not event.streaking:
                # End of streak or single gift
                self.scoring_service.process_gift(
                    unique_id,
                    nickname,
                    event.gift.diamond_count,
                    str(event.gift.id),
                    event.gift.name,
                    event.repeat_count,
                    avatar_url=avatar_url,
                    gift_icon=gift_image,
                )
            elif not event.gift.streakable:
                # Non-streakable
                self.scoring_service.process_gift(
                    unique_id,
                    nickname,
                    event.gift.diamond_count,
                    str(event.gift.id),
                    event.gift.name,
                    1,
                    avatar_url=avatar_url,
                    gift_icon=gift_image,
                )

            # Log for Admin Dashboard
            await self.logging_service.info(
                f"{nickname} sent {event.gift.name} x{event.repeat_count}",
                details={"type": "Gift"},
            )
        except Exception as e:
            await self.log_ingestion_error(
                e,
                {"type": "Gift", "data": str(event)},
            )
            asyncio.create_task(
                self.logging_service.error(f"Error processing gift: {e}", e)
            )

    async def on_comment(self, event: CommentEvent):
        try:
            # CRITICAL: Do not access event.user directly, it raises TypeError.
            # CommentEvent uses event.user_info.
            user = getattr(event, "user_info", None)
            if not user:
                # Try fallback but event.user is known to fail
                user = getattr(event, "user", None)

            if not user:
                await self.logging_service.warning(
                    "CommentEvent received without user info"
                )
                return

            # Robust Attribute Access
            unique_id = getattr(user, "unique_id", getattr(user, "username", None))
            nickname = getattr(user, "nickname", getattr(user, "nick_name", None))

            if not unique_id or not nickname:
                await self.logging_service.warning(
                    f"Incomplete user info in CommentEvent: {unique_id}, {nickname}"
                )
                return

            # Avatar Extraction
            avatar_thumb = getattr(user, "avatar_thumb", None)
            avatar_url = None
            if avatar_thumb:
                if hasattr(avatar_thumb, "m_urls") and avatar_thumb.m_urls:
                    avatar_url = avatar_thumb.m_urls[0]
                elif hasattr(avatar_thumb, "url_list") and avatar_thumb.url_list:
                    avatar_url = avatar_thumb.url_list[0]
                elif hasattr(avatar_thumb, "urls") and avatar_thumb.urls:
                    avatar_url = avatar_thumb.urls[0]

            await self.data_service.upsert_user(unique_id, nickname, avatar_url)
            await self.data_service.save_comment(
                unique_id, self.session_id, event.comment
            )

            self.scoring_service.process_comment(
                unique_id,
                event.comment,
                user_nickname=nickname,
                avatar_url=avatar_url,
            )

            # Log for Admin Dashboard
            await self.logging_service.info(
                f"{nickname}: {event.comment}", details={"type": "Chat"}
            )
        except Exception as e:
            # Do NOT access event.user in error handling
            await self.log_ingestion_error(
                e,
                {
                    "type": "Comment",
                    "comment": event.comment,
                    "data": str(event),
                },
            )
            asyncio.create_task(
                self.logging_service.error(f"Error processing comment: {e}", e)
            )

    async def on_follow(self, event: FollowEvent):
        # Optional: Give points for follow?
        pass

    async def on_share(self, event: ShareEvent):
        # Optional: Give points for share?
        pass
