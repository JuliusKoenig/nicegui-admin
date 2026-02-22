import asyncio
import logging
import traceback
from collections.abc import Callable
from typing import Any

from nicegui import ui, background_tasks
from nicegui.page_arguments import RouteMatch, PageArguments

logger = logging.getLogger(__name__)


class CustomSubPages(ui.sub_pages):
    """
    Custom ui.sub_pages with built-in authentication and custom 404 handling.""
    """

    def __init__(self,
                 routes: dict[str, Callable] | None = None,
                 *,
                 root_path: str | None = None,
                 data: dict[str, Any] | None = None,
                 show_404: bool = True) -> None:
        super().__init__(routes,
                         root_path=root_path,
                         data=data,
                         show_404=show_404)

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
        self.error_page(title="404 - Page Not Found",
                        icon="search_off",
                        color="red",
                        message=f"The page '{self._router.current_path}' does not exist.",
                        buttons=True,
                        log=True)

    def _render_error(self, error: Exception) -> None:
        title = "500 - Internal Server Error"
        message = f"The page '{self._router.current_path}' produced an error."
        stack_trace = None
        # ToDo: show stack_trace only on  if debug
        stack_trace = traceback.format_exc()

        self.error_page(title=title,
                        icon="error_outline",
                        color="red",
                        message=message,
                        stack_trace=stack_trace,
                        buttons=True,
                        log=True)

    def _set_match(self, match: RouteMatch | None) -> None:
        super()._set_match(match=match)
        self.has_404 = False

    def error_page(self,
                   title: str,
                   icon: str | None = None,
                   color: str | None = "red",
                   message: str | None = None,
                   stack_trace: str | None = None,
                   buttons: bool = True,
                   log: bool = True) -> None:
        self.clear()
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
        logger.error(log_msg)


custom_sub_pages = CustomSubPages
