import inspect
import json
from TikTokLive.events import (
    CommentEvent,
    GiftEvent,
    LikeEvent,
    ConnectEvent,
    DisconnectEvent,
    ShareEvent,
    FollowEvent,
    JoinEvent,
    ViewerUpdateEvent,
)
from TikTokLive.proto.tiktok_schema_pb2 import WebcastGiftMessage


def get_attributes(cls):
    attributes = {}
    for name, kind in inspect.getmembers(cls):
        if (
            not name.startswith("__")
            and not inspect.ismethod(kind)
            and not inspect.isfunction(kind)
        ):
            # Try to get type hint
            type_hint = str(type(kind))
            if hasattr(kind, "__annotations__"):
                type_hint = str(kind.__annotations__)
            attributes[name] = str(kind)
    return attributes


def inspect_event(event_cls):
    print(f"## {event_cls.__name__}")
    print("| Attribute | Type/Value | Description |")
    print("| :--- | :--- | :--- |")

    # Inspect annotations if available (Pydantic/Dataclasses)
    if hasattr(event_cls, "__annotations__"):
        for name, type_hint in event_cls.__annotations__.items():
            print(f"| `{name}` | `{type_hint}` | - |")

    # Inspect __dict__ for other properties
    # This is tricky without an instance.
    # Let's try to inspect the source or docstring if possible.
    doc = inspect.getdoc(event_cls)
    if doc:
        print(f"\n**Docstring:**\n{doc}\n")
    print("\n")


def main():
    events = [
        CommentEvent,
        GiftEvent,
        LikeEvent,
        ConnectEvent,
        DisconnectEvent,
        ShareEvent,
        FollowEvent,
        JoinEvent,
        ViewerUpdateEvent,
    ]

    print("# TikTokLive Event Attributes\n")
    for evt in events:
        inspect_event(evt)

    # Also check ImageModel if we can find it
    # It's usually nested in User or Gift
    print("## ImageModel Inspection (Attempt)")
    try:
        from TikTokLive.types import ImageModel

        inspect_event(ImageModel)
        print("ImageModel found in types.")
    except ImportError:
        print("ImageModel not found in types. Checking event nesting...")


if __name__ == "__main__":
    main()
