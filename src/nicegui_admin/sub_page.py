import asyncio
import logging
import traceback
from collections.abc import Callable
from functools import wraps
from pathlib import Path
from typing import Any, Awaitable

from nicegui import ui, background_tasks
from nicegui.helpers import is_coroutine_function
from nicegui.page_arguments import RouteMatch, PageArguments

from nicegui_admin.helpers import Unset, prettify_name, get_from_stack, SearchTarget

logger = logging.getLogger(__name__)


class SubPages(ui.sub_pages):
    def __init__(self) -> None:
        self._sub_page_handler: "SubPageHandler" = get_from_stack(SearchTarget(subtype=SubPageHandler),
                                                                  context=2)
        # ToDo: Use data to pass models direct to the sub page builders without having to use global variables or other workarounds
        super().__init__()

    @property
    def sub_page_handler(self) -> "SubPageHandler":
        return self._sub_page_handler

    @property
    def _404_enabled(self) -> bool:
        return self.sub_page_handler.show_404

    @_404_enabled.setter
    def _404_enabled(self, value: bool) -> None:
        ...

    @property
    def _routes(self) -> dict[str, Callable]:
        return {sub_page["path"]: sub_page["builder"] for sub_page in self.sub_page_handler._sub_pages}

    @_routes.setter
    def _routes(self, value: dict[str, Callable]) -> None:
        ...

    def _render_page(self, match: RouteMatch) -> bool:
        kwargs = PageArguments.build_kwargs(match, self, self._data)
        self._rendered_path = f'{self._root_path or ""}{match.path}'
        try:
            result = match.builder(**kwargs)
        except Exception as e:
            self._render_error(e)
            self.client.handle_exception(e)
            return True

        self._handle_scrolling(match, behavior="instant")
        if asyncio.iscoroutine(result):
            async def background_task():
                with self:
                    try:
                        await result
                    except Exception as e:
                        self._render_error(e)
                        self.client.handle_exception(e)

            task = background_tasks.create(background_task(), name=f"building sub_page {match.pattern}")
            self._active_tasks.add(task)

            def _close_if_canceled(t: asyncio.Task) -> None:
                if t.cancelled():
                    result.close()
                self._active_tasks.discard(t)

            task.add_done_callback(_close_if_canceled)
        return True

    def _render_404(self) -> None:
        self.clear()
        self.sub_page_handler.error_page(title="404 - Page Not Found",
                                         icon="search_off",
                                         color="red",
                                         message=f"The page '{self._router.current_path}' does not exist.",
                                         buttons=True,
                                         log=True)

    def _render_error(self, error: Exception) -> None:
        self.clear()
        title = "500 - Internal Server Error"
        message = f"The page '{self._router.current_path}' produced an error."
        stack_trace = None
        # ToDo: show stack_trace only on  if debug
        stack_trace = traceback.format_exc()

        self.sub_page_handler.error_page(title=title,
                                         icon="error_outline",
                                         color="red",
                                         message=message,
                                         stack_trace=stack_trace,
                                         buttons=True,
                                         log=True)

    def _set_match(self, match: RouteMatch | None) -> None:
        super()._set_match(match=match)
        self.has_404 = False


class SubPageHandler:
    def __init__(self,
                 show_404: bool = True,
                 sub_pages_cls: type[SubPages] = SubPages) -> None:
        self.show_404: bool = show_404
        self._sub_pages_cls: type[SubPages] = sub_pages_cls
        self._sub_pages: list[dict[str, Any]] = []

    @property
    def sub_pages(self) -> dict[str, Any]:
        """
        All sub pages added to the sub page handler.

        :return: Tuple of all sub pages added to the sub page handler.
        """

        return {sub_page["path"]: {"builder": sub_page["builder"],
                                   "title": sub_page["title"],
                                   "icon": sub_page["icon"]} for sub_page in self._sub_pages}

    @property
    def sub_page_cls(self) -> type[SubPages]:
        """
        SubPages class used by the sub page handler.

        :return: SubPages class used by the sub page handler.
        """

        return self._sub_pages_cls

    def sub_page(self,
                 path: str,
                 *,
                 title: str | None = Unset,
                 icon: str | Path | None = None) -> Callable[..., Any] | Callable[..., Awaitable[Any]]:
        """
        Decorator for adding a sub page to the sub page handler.

        :param path: Path of the sub page. Should be unique among all sub pages added to the sub page handler.
        :param title: Title of the sub page. If not provided, the title will be inferred from the builder function name.
        :param icon: Icon of the sub page. Can be either a URL or a local file path. If not provided, no icon will be set for the sub page.
        :return: Decorator function that takes a builder function and adds it as a sub page to the sub page handler.
        """

        def decorator(builder: Callable[..., Any] | Callable[..., Awaitable[Any]]) -> Callable[..., Any] | Callable[
            ..., Awaitable[Any]]:
            self.add_sub_page(path=path,
                              builder=builder,
                              title=title,
                              icon=icon)
            return builder

        return decorator

    # rename favicon to icon
    def add_sub_page(self,
                     path: str,
                     builder: Callable,
                     *,
                     title: str | None = Unset,
                     icon: str | Path | None = None) -> None:
        """
        Add a sub page to the sub page handler.

        :param path: Path of the sub page. Should be unique among all sub pages added to the sub page handler.
        :param builder: Builder function for the sub page. Can be either a regular function or an async function that builds the page content when called.
        :param title: Title of the sub page. If not provided, the title will be inferred from the builder function name.
        :param icon: Icon of the sub page. Can be either a URL or a local file path. If not provided, no icon will be set for the sub page.
        :return: None
        """

        title = Unset.resolve(title, prettify_name(builder.__name__))
        if path in self.sub_pages:
            raise ValueError(f"A sub page with path '{path}' is already registered.")
        if is_coroutine_function(builder):
            @wraps(builder)
            async def wrapper(*args, **kwargs):
                if title is not Unset:
                    ui.page_title(title)
                # ToDo: implement favicon handling
                return await builder(*args, **kwargs)
        else:
            @wraps(builder)
            def wrapper(*args, **kwargs):
                if title is not Unset:
                    ui.page_title(title)
                # ToDo: implement favicon handling
                return builder(*args, **kwargs)
        self._sub_pages.append({"path": path,
                                "builder": wrapper,
                                "title": title,
                                "icon": icon})

    def error_page(self,
                   title: str,
                   icon: str | None = None,
                   color: str | None = "red",
                   message: str | None = None,
                   stack_trace: str | None = None,
                   buttons: bool = True,
                   log: bool = True) -> None:
        # ToDo: implement favicon for error pages
        ui.page_title(title)
        log_msg = title
        with (ui.column().classes("absolute-center items-center")):
            if icon is not None:
                _icon = ui.icon(icon, size="4rem")
                if color is not None:
                    _icon.classes(f"text-{color}")
            _title = ui.label(title).classes("text-2xl")
            if color is not None:
                _title.classes(f"text-{color}")
            ui.label().classes("text-gray-600")
            if message is not None:
                ui.label(message).classes("text-gray-600")
                log_msg += f" -> {message}"
            if stack_trace is not None:
                ui.code(stack_trace)
                log_msg += f"\n{stack_trace}"
            if buttons:
                with ui.row().classes("mt-4"):
                    ui.button("Go Home", icon="home", on_click=lambda: ui.navigate.to("/")).props("outline")
                    ui.button("Go Back", icon="arrow_back", on_click=ui.navigate.back).props("outline")
        if log:
            logger.error(log_msg)
