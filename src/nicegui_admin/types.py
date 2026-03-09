from enum import Enum
from typing import Literal, Callable, Any, Awaitable

SyncFunction = Callable[..., Any]
AsyncFunction = Callable[..., Awaitable[Any]]
SyncOrAsyncFunction = SyncFunction | AsyncFunction

class ExportType(str, Enum):
    """Enumeration of string constants that represent different export types."""

    CSV = "csv"
    EXCEL = "excel"
    PDF = "pdf"
    PRINT = "print"
