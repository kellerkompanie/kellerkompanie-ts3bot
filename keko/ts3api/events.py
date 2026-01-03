"""TS3 Event definitions using dataclasses."""

from dataclasses import dataclass, field
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class TargetMode(Enum):
    """Text message target mode."""

    PRIVATE = 1
    CHANNEL = 2
    SERVER = 3


@dataclass(frozen=True, slots=True)
class TS3Event:
    """Base class for all TS3 events."""

    raw_data: dict[str, str] = field(repr=False)


@dataclass(frozen=True, slots=True)
class TextMessageEvent(TS3Event):
    """Text message received event."""

    target_mode: TargetMode
    message: str
    invoker_id: int
    invoker_name: str
    invoker_uid: str
    target: int | None = None


@dataclass(frozen=True, slots=True)
class ClientEnteredEvent(TS3Event):
    """Client connected to server."""

    client_id: int
    client_name: str
    client_uid: str
    client_dbid: int
    target_channel_id: int
    from_channel_id: int
    reason_id: int
    client_description: str = ""
    client_country: str = ""
    client_away: bool = False
    client_away_message: str = ""
    client_servergroups: str = ""
    client_input_muted: bool = False
    client_output_muted: bool = False
    client_is_recording: bool = False


@dataclass(frozen=True, slots=True)
class ClientLeftEvent(TS3Event):
    """Client disconnected from server."""

    client_id: int
    target_channel_id: int
    from_channel_id: int
    reason_id: int
    reason_message: str = ""


@dataclass(frozen=True, slots=True)
class ClientMovedEvent(TS3Event):
    """Client was moved by another user."""

    client_id: int
    target_channel_id: int
    reason_id: int
    invoker_id: int
    invoker_name: str
    invoker_uid: str


@dataclass(frozen=True, slots=True)
class ClientMovedSelfEvent(TS3Event):
    """Client moved themselves."""

    client_id: int
    target_channel_id: int
    reason_id: int


@dataclass(frozen=True, slots=True)
class ChannelEditedEvent(TS3Event):
    """Channel was edited."""

    channel_id: int
    invoker_id: int
    invoker_name: str
    invoker_uid: str
    reason_id: int
    channel_topic: str = ""


@dataclass(frozen=True, slots=True)
class ChannelDescriptionEditedEvent(TS3Event):
    """Channel description was changed."""

    channel_id: int


@dataclass(frozen=True, slots=True)
class ServerEditedEvent(TS3Event):
    """Server settings were edited."""

    invoker_id: int
    invoker_name: str
    invoker_uid: str
    reason_id: int
    changed_properties: dict[str, str] = field(default_factory=dict)


def _int(value: str, default: int = -1) -> int:
    """Parse int with default fallback."""
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def _bool(value: str) -> bool:
    """Parse bool from string '0' or '1'."""
    return value == "1"


def parse_event(event_type: str, data: dict[str, str]) -> TS3Event | None:
    """Parse raw event data into typed event object."""
    match event_type:
        case "notifytextmessage":
            mode_val = _int(data.get("targetmode", "1"), 1)
            try:
                target_mode = TargetMode(mode_val)
            except ValueError:
                target_mode = TargetMode.PRIVATE
            return TextMessageEvent(
                raw_data=data,
                target_mode=target_mode,
                message=data.get("msg", ""),
                invoker_id=_int(data.get("invokerid", "-1")),
                invoker_name=data.get("invokername", ""),
                invoker_uid=data.get("invokeruid", ""),
                target=_int(data["target"]) if "target" in data else None,
            )

        case "notifycliententerview":
            return ClientEnteredEvent(
                raw_data=data,
                client_id=_int(data.get("clid", "-1")),
                client_name=data.get("client_nickname", ""),
                client_uid=data.get("client_unique_identifier", ""),
                client_dbid=_int(data.get("client_database_id", "-1")),
                target_channel_id=_int(data.get("ctid", "-1")),
                from_channel_id=_int(data.get("cfid", "-1")),
                reason_id=_int(data.get("reasonid", "-1")),
                client_description=data.get("client_description", ""),
                client_country=data.get("client_country", ""),
                client_away=_bool(data.get("client_away", "0")),
                client_away_message=data.get("client_away_message", ""),
                client_servergroups=data.get("client_servergroups", ""),
                client_input_muted=_bool(data.get("client_input_muted", "0")),
                client_output_muted=_bool(data.get("client_output_muted", "0")),
                client_is_recording=_bool(data.get("client_is_recording", "0")),
            )

        case "notifyclientleftview":
            return ClientLeftEvent(
                raw_data=data,
                client_id=_int(data.get("clid", "-1")),
                target_channel_id=_int(data.get("ctid", "-1")),
                from_channel_id=_int(data.get("cfid", "-1")),
                reason_id=_int(data.get("reasonid", "-1")),
                reason_message=data.get("reasonmsg", ""),
            )

        case "notifyclientmoved":
            if "invokerid" in data:
                return ClientMovedEvent(
                    raw_data=data,
                    client_id=_int(data.get("clid", "-1")),
                    target_channel_id=_int(data.get("ctid", "-1")),
                    reason_id=_int(data.get("reasonid", "-1")),
                    invoker_id=_int(data.get("invokerid", "-1")),
                    invoker_name=data.get("invokername", ""),
                    invoker_uid=data.get("invokeruid", ""),
                )
            else:
                return ClientMovedSelfEvent(
                    raw_data=data,
                    client_id=_int(data.get("clid", "-1")),
                    target_channel_id=_int(data.get("ctid", "-1")),
                    reason_id=_int(data.get("reasonid", "-1")),
                )

        case "notifychanneledited":
            return ChannelEditedEvent(
                raw_data=data,
                channel_id=_int(data.get("cid", "-1")),
                invoker_id=_int(data.get("invokerid", "-1")),
                invoker_name=data.get("invokername", ""),
                invoker_uid=data.get("invokeruid", ""),
                reason_id=_int(data.get("reasonid", "-1")),
                channel_topic=data.get("channel_topic", ""),
            )

        case "notifychanneldescriptionchanged":
            return ChannelDescriptionEditedEvent(
                raw_data=data,
                channel_id=_int(data.get("cid", "-1")),
            )

        case "notifyserveredited":
            known_keys = {"reasonid", "invokerid", "invokeruid", "invokername"}
            changed = {k: v for k, v in data.items() if k not in known_keys}
            return ServerEditedEvent(
                raw_data=data,
                invoker_id=_int(data.get("invokerid", "-1")),
                invoker_name=data.get("invokername", ""),
                invoker_uid=data.get("invokeruid", ""),
                reason_id=_int(data.get("reasonid", "-1")),
                changed_properties=changed,
            )

        case _:
            logger.warning(f"Unknown event type: {event_type}")
            return None
