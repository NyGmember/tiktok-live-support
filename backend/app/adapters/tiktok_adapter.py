import asyncio
from TikTokLive import TikTokLiveClient
from TikTokLive.events import CommentEvent, GiftEvent, LikeEvent, ConnectEvent, DisconnectEvent, ShareEvent, FollowEvent
from app.services.scoring_service import ScoringService
from app.services.logging_service import LoggingService

class TikTokLiveAdapter:
    def __init__(self, scoring_service: ScoringService, logging_service: LoggingService, unique_id: str):
        self.scoring_service = scoring_service
        self.logging_service = logging_service
        self.unique_id = unique_id
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

    async def start(self):
        self.is_running = True
        await self.logging_service.info(f"Starting TikTokLiveAdapter for {self.unique_id}")
        
        # Loop to keep checking if live
        while self.is_running:
            try:
                if not await self.client.is_live():
                    await self.logging_service.info(f"{self.unique_id} is offline. Retrying in 30s...")
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
            # Logic from capture_live.py
            is_follower = False
            if hasattr(event.user, 'is_follower'):
                is_follower = event.user.is_follower
            
            self.scoring_service.process_like(event.user.unique_id, event.user.nickname, event.count, is_follower)
        except Exception as e:
            asyncio.create_task(self.logging_service.error(f"Error processing like: {e}", e))

    async def on_gift(self, event: GiftEvent):
        try:
            if event.gift.streakable and not event.streaking:
                # End of streak or single gift
                self.scoring_service.process_gift(
                    event.user.unique_id, 
                    event.user.nickname, 
                    event.gift.diamond_count, 
                    str(event.gift.id), 
                    event.gift.name, 
                    event.repeat_count
                )
            elif not event.gift.streakable:
                # Non-streakable
                self.scoring_service.process_gift(
                    event.user.unique_id, 
                    event.user.nickname, 
                    event.gift.diamond_count, 
                    str(event.gift.id), 
                    event.gift.name, 
                    1
                )
        except Exception as e:
            asyncio.create_task(self.logging_service.error(f"Error processing gift: {e}", e))

    async def on_comment(self, event: CommentEvent):
        try:
            self.scoring_service.process_comment(event.user.unique_id, event.comment)
        except Exception as e:
            asyncio.create_task(self.logging_service.error(f"Error processing comment: {e}", e))

    async def on_follow(self, event: FollowEvent):
        # Optional: Give points for follow?
        pass

    async def on_share(self, event: ShareEvent):
        # Optional: Give points for share?
        pass
