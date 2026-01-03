"""
keko.ts3api - Modern async TeamSpeak 3 Query API library.

Usage:
    from keko.ts3api import TS3Connection

    async with TS3Connection("localhost", 10011) as conn:
        await conn.login("serveradmin", "password")
        await conn.use(1)

        await conn.register_for_server_events()
        await conn.register_for_private_messages()

        async for event in conn.events():
            handle_event(event)
"""

from keko.ts3api.connection import TS3Connection
from keko.ts3api.events import (
    ChannelDescriptionEditedEvent,
    ChannelEditedEvent,
    ClientEnteredEvent,
    ClientLeftEvent,
    ClientMovedEvent,
    ClientMovedSelfEvent,
    ServerEditedEvent,
    TargetMode,
    TextMessageEvent,
    TS3Event,
)
from keko.ts3api.exceptions import (
    TS3ConnectionError,
    TS3Error,
    TS3QueryError,
    TS3TimeoutError,
)
from keko.ts3api.types import TS3ErrorCode

__all__ = [
    # Connection
    "TS3Connection",
    # Events
    "TS3Event",
    "TextMessageEvent",
    "ClientEnteredEvent",
    "ClientLeftEvent",
    "ClientMovedEvent",
    "ClientMovedSelfEvent",
    "ChannelEditedEvent",
    "ChannelDescriptionEditedEvent",
    "ServerEditedEvent",
    "TargetMode",
    # Exceptions
    "TS3Error",
    "TS3ConnectionError",
    "TS3QueryError",
    "TS3TimeoutError",
    # Types
    "TS3ErrorCode",
]

__version__ = "2.0.0"
