"""TS3 API Exceptions."""

from keko.ts3api.protocol import unescape
from keko.ts3api.types import TS3ErrorCode


class TS3Error(Exception):
    """Base exception for TS3 API errors."""

    pass


class TS3ConnectionError(TS3Error):
    """Connection-related errors (timeout, disconnect, etc.)."""

    pass


class TS3TimeoutError(TS3ConnectionError):
    """Operation timed out."""

    pass


class TS3QueryError(TS3Error):
    """Query command failed with an error response from server."""

    def __init__(self, error_id: int, message: str) -> None:
        try:
            self.error_code = TS3ErrorCode(error_id)
        except ValueError:
            self.error_code = TS3ErrorCode.UNDEFINED
        self.error_id = error_id
        self.error_message = unescape(message)
        super().__init__(f"Query failed: id={error_id} msg={self.error_message}")
