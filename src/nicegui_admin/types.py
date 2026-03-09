from typing import Literal, Callable, Any, Awaitable

SyncFunction = Callable[..., Any]
AsyncFunction = Callable[..., Awaitable[Any]]
SyncOrAsyncFunction = SyncFunction | AsyncFunction
