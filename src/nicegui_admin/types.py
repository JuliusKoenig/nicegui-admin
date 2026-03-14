from enum import Enum
from typing import Callable, Any, Awaitable

SyncMethod = Callable[..., Any]
AsyncMethod = Callable[..., Awaitable[Any]]
SyncOrAsyncMethod = SyncMethod | AsyncMethod

FieldGetterMethodResult = Any
FieldGetterMethod = Callable[[], Awaitable[FieldGetterMethodResult]]
FieldValidatorMethodResult = None | str
FieldValidatorMethod = Callable[[], Awaitable[FieldValidatorMethodResult]]
FieldRenderResult = None | tuple[FieldGetterMethod, FieldValidatorMethod]


class ExportType(str, Enum):
    """Enumeration of string constants that represent different export types."""

    CSV = "csv"
    EXCEL = "excel"
    PDF = "pdf"
    PRINT = "print"
