from enum import Enum
from typing import Callable, Any, Awaitable, Optional

SyncMethod = Callable[..., Any]
AsyncMethod = Callable[..., Awaitable[Any]]
SyncOrAsyncMethod = SyncMethod | AsyncMethod


class ExportType(str, Enum):
    """Enumeration of string constants that represent different export types."""

    CSV = "csv"
    EXCEL = "excel"
    PDF = "pdf"
    PRINT = "print"


# --- Field types ---

class FieldDefault(str, Enum):
    STATIC = "static"
    DYNAMIC = "dynamic"


class FieldInputContentType(str, Enum):
    TEXT = "text"
    PASSWORD = "password"
    TEXTAREA = "textarea"
    EMAIL = "email"
    SEARCH = "search"
    TEL = "tel"
    FILE = "file"
    NUMBER = "number"
    URL = "url"
    TIME = "time"
    DATE = "date"
    DATETIME_LOCAL = "datetime-local"


class FieldInputLabelFormValue(str, Enum):
    LABEL = "label"
    HELP_TEXT = "help_text"
