from pathlib import Path
from typing import Any, Callable

from nicegui import APIRouter
from nicegui.page import page
from nicegui.language import Language



class Page(page):
    def __init__(self,
                 path: str, *,
                 title: str | None = None,
                 viewport: str | None = None,
                 favicon: str | Path | None = None,
                 dark: bool | None = ...,  # type: ignore
                 language: Language = ...,  # type: ignore
                 response_timeout: float = 3.0,
                 reconnect_timeout: float | None = None,
                 api_router: APIRouter | None = None,
                 **kwargs: Any,
                 ) -> None:
        super().__init__(path=path,
                         title=title,
                         viewport=viewport,
                         favicon=favicon,
                         dark=dark,
                         language=language,
                         response_timeout=response_timeout,
                         reconnect_timeout=reconnect_timeout,
                         api_router=api_router,
                         **kwargs)

    def _wrap(self,
              func: Callable[..., Any]) -> Callable[..., Any]:
        return super()._wrap(func=func)
