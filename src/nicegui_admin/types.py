from enum import Enum
from typing import Callable, Any, Awaitable, Optional


SyncMethod = Callable[..., Any]
AsyncMethod = Callable[..., Awaitable[Any]]
SyncOrAsyncMethod = SyncMethod | AsyncMethod

FieldFormGetter = Optional[Callable[[], Any]]
FieldRenderResult = Optional[FieldFormGetter]


class ExportType(str, Enum):
    """Enumeration of string constants that represent different export types."""

    CSV = "csv"
    EXCEL = "excel"
    PDF = "pdf"
    PRINT = "print"
