from sqlalchemy.future import select
from sqlalchemy.dialects.postgresql import insert
from app.models.base import AsyncSessionLocal
from app.models.user import User
from app.models.gift import Gift
from app.models.comment import Comment
from datetime import datetime


class DataService:
    async def upsert_user(self, tiktok_id: str, nickname: str, avatar_url: str = None):
        async with AsyncSessionLocal() as session:
            try:
                # Check if user exists
                result = await session.execute(
                    select(User).where(User.tiktok_id == tiktok_id)
                )
                user = result.scalar_one_or_none()

                if user:
                    # Update info if changed
                    if user.nickname != nickname or (
                        avatar_url and user.avatar_url != avatar_url
                    ):
                        user.nickname = nickname
                        if avatar_url:
                            user.avatar_url = avatar_url
                        user.updated_at = datetime.utcnow()
                        await session.commit()
                else:
                    # Create new user
                    new_user = User(
                        tiktok_id=tiktok_id, nickname=nickname, avatar_url=avatar_url
                    )
                    session.add(new_user)
                    await session.commit()
            except Exception as e:
                print(f"Error upserting user: {e}")
                await session.rollback()

    async def upsert_gift(
        self, gift_id: str, name: str, diamond_count: int, image_url: str = None
    ):
        async with AsyncSessionLocal() as session:
            try:
                result = await session.execute(
                    select(Gift).where(Gift.gift_id == gift_id)
                )
                gift = result.scalar_one_or_none()

                if not gift:
                    new_gift = Gift(
                        gift_id=gift_id,
                        name=name,
                        diamond_count=diamond_count,
                        image_url=image_url,
                    )
                    session.add(new_gift)
                    await session.commit()
                elif gift.image_url is None and image_url:
                    gift.image_url = image_url
                    await session.commit()

            except Exception as e:
                print(f"Error upserting gift: {e}")
                await session.rollback()

    async def save_comment(self, user_id: str, session_id: str, content: str):
        async with AsyncSessionLocal() as session:
            try:
                new_comment = Comment(
                    user_id=user_id, session_id=session_id, content=content
                )
                session.add(new_comment)
                await session.commit()
            except Exception as e:
                print(f"Error saving comment: {e}")
                await session.rollback()

    async def get_user_comments(self, user_id: str, session_id: str):
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(Comment)
                .where(Comment.user_id == user_id)
                .where(Comment.session_id == session_id)
                .where(Comment.is_used == False)
                .order_by(Comment.timestamp.desc())
            )
            return result.scalars().all()

    async def mark_comment_as_used(self, comment_id: int):
        async with AsyncSessionLocal() as session:
            try:
                result = await session.execute(
                    select(Comment).where(Comment.id == comment_id)
                )
                comment = result.scalar_one_or_none()
                if comment:
                    comment.is_used = True
                    await session.commit()
            except Exception as e:
                print(f"Error marking comment as used: {e}")
                await session.rollback()
