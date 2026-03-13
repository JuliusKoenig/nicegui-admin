from enum import Enum
from typing import Callable, Any, Awaitable

from nicegui.element import Element

SyncFunction = Callable[..., Any]
AsyncFunction = Callable[..., Awaitable[Any]]
SyncOrAsyncFunction = SyncFunction | AsyncFunction
FieldRenderFunctionResult = dict[str, Element]
FieldRenderFunction = Callable[..., Awaitable[FieldRenderFunctionResult]]

class ExportType(str, Enum):
    """Enumeration of string constants that represent different export types."""

    CSV = "csv"
    EXCEL = "excel"
    PDF = "pdf"
    PRINT = "print"
