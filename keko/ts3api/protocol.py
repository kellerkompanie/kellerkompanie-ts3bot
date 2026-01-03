"""TS3 Query Protocol utilities."""

from typing import Final

# Don't change the order in this map, otherwise it might break
_ESCAPE_MAP: Final[list[tuple[str, str]]] = [
    ("\\", r"\\"),
    ("/", r"\/"),
    (" ", r"\s"),
    ("|", r"\p"),
    ("\a", r"\a"),
    ("\b", r"\b"),
    ("\f", r"\f"),
    ("\n", r"\n"),
    ("\r", r"\r"),
    ("\t", r"\t"),
    ("\v", r"\v"),
]


def escape(raw: str) -> str:
    """Escape special characters for TS3 protocol."""
    for char, replacement in _ESCAPE_MAP:
        raw = raw.replace(char, replacement)
    return raw


def unescape(raw: str) -> str:
    """Unescape TS3 protocol characters."""
    for replacement, char in reversed(_ESCAPE_MAP):
        raw = raw.replace(char, replacement)
    return raw


def parse_response_to_dict(response: str) -> dict[str, str]:
    """Parse a single TS3 response line to dictionary."""
    result: dict[str, str] = {}
    for part in response.split(" "):
        if "=" in part:
            key, value = part.split("=", 1)
            result[key] = unescape(value)
        elif part:
            # Flag without value
            result[part] = ""
    return result


def parse_response_to_list(response: str) -> list[dict[str, str]]:
    """Parse TS3 response with multiple items (pipe-separated) to list of dicts."""
    return [parse_response_to_dict(item) for item in response.split("|") if item]


def build_command(command: str, *args: str, **kwargs: str | int) -> bytes:
    """Build a TS3 command string with proper escaping."""
    parts = [command]
    parts.extend(f"-{arg}" for arg in args)
    parts.extend(f"{k}={escape(str(v))}" for k, v in kwargs.items())
    return (" ".join(parts) + "\n\r").encode("utf-8")
