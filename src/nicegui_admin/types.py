from typing import Literal, Callable, Any, Awaitable

FieldModes = Literal["list", "detail", "create", "edit"]
SyncOrAsyncFunction = Callable[..., Any] | Callable[..., Awaitable[Any]]
