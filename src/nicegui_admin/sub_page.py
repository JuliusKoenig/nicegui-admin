import asyncio
import logging
import traceback
from pathlib import Path
from typing import Any, Callable, Optional

from nicegui import app, APIRouter
from nicegui import ui, background_tasks
from nicegui.page_arguments import RouteMatch, PageArguments

from nicegui_admin.helpers import DecoratedMethodClass, decorate, Unset, prettify_name
from nicegui_admin.types import SyncOrAsyncFunction

logger = logging.getLogger(__name__)


def subpage(path: str,
            *,
            title: str | None = Unset,
            icon: str | Path | None = None):
    return decorate("subpage",
                    path=path,
                    title=title,
                    icon=icon)


class SubPageRouter(DecoratedMethodClass):
    class SubPages(ui.sub_pages):
        def __init__(self, subpage_router: "SubPageRouter") -> None:
            self.subpage_router: "SubPageRouter" = subpage_router
            super().__init__(show_404=self.subpage_router.show_404)

        @property
        def _routes(self) -> dict[str, SyncOrAsyncFunction]:
            routes = {}
            for router in self.subpage_router.subpage_router:
                routes[router.prefix] = router.root
            for path, kwargs in self.subpage_router.subpages.items():
                if self._root_path is not None:
                    path = path[len(self._root_path):] if path.startswith(self._root_path) else path
                builder: SyncOrAsyncFunction = kwargs["builder"]
                routes[path] = builder
            return routes

        @property
        def _builder_attributes(self) -> dict[SyncOrAsyncFunction, dict[str, Any]]:
            builder_attributes = {}
            for path, kwargs in self.subpage_router.subpages.items():
                builder_attributes[kwargs["builder"]] = kwargs
            return builder_attributes

        @_routes.setter
        def _routes(self, value: dict[str, Callable]) -> None:
            ...

        def _render_page(self, match: RouteMatch) -> bool:
            kwargs = PageArguments.build_kwargs(match, self, self._data)
            self._rendered_path = f'{self._root_path or ""}{match.path}'
            try:
                builder_attributes = self._builder_attributes.get(match.builder, {})
                title = builder_attributes.get("title")
                if title is not None:
                    ui.page_title(title)
                icon = builder_attributes.get("icon")
                if icon is not None:
                    # ToDo: support favicon for sub pages
                    logger.warning(f"Favicon for sub pages is not yet supported. Ignoring icon '{icon}' for page '{match.path}'.")
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
            self.subpage_router.error_page(title=f"404 - Page Not Found",
                                           icon="search_off",
                                           color="red",
                                           message=f"The page '{self._router.current_path}' does not exist.",
                                           buttons=True,
                                           log=True)

        def _render_error(self, error: Exception) -> None:
            self.clear()
            self.subpage_router.error_page(title="500 - Internal Server Error",
                                           icon="error_outline",
                                           color="red",
                                           message=f"The page '{self._router.current_path}' produced an error.",
                                           error=error,
                                           buttons=True,
                                           log=True)

        def _set_match(self, match: RouteMatch | None) -> None:
            super()._set_match(match=match)
            self.has_404 = False

    def __init__(self,
                 prefix: str = "",
                 show_404: bool = True) -> None:
        self._parent_router: Optional[SubPageRouter] = None
        self._subpage_router: list[SubPageRouter] = []
        self._prefix = prefix
        self.prefix = prefix  # validate prefix
        self.show_404: bool = show_404

    @property
    def sub_page_app(self) -> "SubPageApp":
        sub_page_app = self
        if self.parent_router is not None:
            sub_page_app = self.parent_router.sub_page_app
        if not isinstance(sub_page_app, SubPageApp):
            raise RuntimeError("The router is not included in a SubPageApp instance. "
                               "Please include the router in a SubPageApp instance using the 'include_subpage_router' method.")
        return sub_page_app

    @property
    def parent_router(self) -> Optional["SubPageRouter"]:
        return self._parent_router

    @property
    def subpage_router(self) -> tuple["SubPageRouter", ...]:
        return tuple(self._subpage_router)

    @property
    def prefix(self) -> str:
        if self.parent_router is not None:
            return self.parent_router.prefix + self._prefix
        return self._prefix

    @prefix.setter
    def prefix(self, value: str) -> None:
        if value:
            assert value.startswith("/"), "A path prefix must start with '/'"
            assert not value.endswith("/"), (
                "A path prefix must not end with '/', as the routes will start with '/'"
            )
        self._prefix = value

    @property
    def subpages(self) -> dict[str, dict[str, Any]]:
        """
        All sub pages added to the sub page handler.

        :return: Tuple of all sub pages added to the sub page handler.
        """

        subpages = {}
        for builder, kwargs in self.__decorated_methods__.get("subpage", {}).items():
            path = self.prefix + kwargs["path"]
            title = Unset.resolve(kwargs["title"], prettify_name(builder.__name__))
            icon = kwargs["icon"]
            subpages[path] = {"builder": builder,
                              "title": title,
                              "icon": icon}

        return subpages

    def subpage(self,
                path: str,
                *,
                title: str | None = Unset,
                icon: str | Path | None = None) -> SyncOrAsyncFunction:
        """
        Decorator for adding a sub page to the sub page handler.

        :param path: Path of the sub page. Should be unique among all sub pages added to the sub page handler.
        :param title: Title of the sub page. If not provided, the title will be inferred from the builder function name.
        :param icon: Icon of the sub page. Can be either a URL or a local file path. If not provided, no icon will be set for the sub page.
        :return: Decorator function that takes a builder function and adds it as a sub page to the sub page handler.
        """

        return self.__decorate__("subpage",
                                 path=path,
                                 title=title,
                                 icon=icon)

    # rename favicon to icon
    def add_subpage(self,
                    builder: SyncOrAsyncFunction,
                    path: str,
                    *,
                    title: str | None = Unset,
                    icon: str | Path | None = None) -> None:
        """
        Add a sub page to the sub page handler.

        :param builder: Builder function for the sub page. Can be either a regular function or an async function that builds the page content when called.
        :param path: Path of the sub page. Should be unique among all sub pages added to the sub page handler.
        :param title: Title of the sub page. If not provided, the title will be inferred from the builder function name.
        :param icon: Icon of the sub page. Can be either a URL or a local file path. If not provided, no icon will be set for the sub page.
        :return: None
        """

        self.__add_decoration__(builder,
                                "subpage",
                                path=path,
                                title=title,
                                icon=icon)

    def include_subpage_router(self,
                               router: "SubPageRouter",
                               *,
                               prefix: str | Unset = Unset) -> None:
        if self is router:
            ValueError("Cannot include the same SupPageRouter instance into itself. "
                       "Did you mean to include a different router?")
        if router in self._subpage_router:
            ValueError("Cannot include SubPageRouter instance that is already included in this router.")
        if router.parent_router is not None:
            ValueError("Cannot include SubPageRouter instance that is already included in another router.")
        if prefix is not Unset:
            router.prefix = prefix
        self._subpage_router.append(router)
        router._parent_router = self

    async def root(self):
        ui.label("Router: " + self.__class__.__name__)
        ui.label("Prefix: " + self.prefix)
        ui.label("Sub Pages:")
        for path, kwargs in self.subpages.items():
            ui.link(kwargs["title"], target=path)
        ui.label("Included SubPageRouters:")
        for router in self.subpage_router:
            ui.link(router.__class__.__name__, target=router.prefix)

        self.SubPages(self)

    def error_page(self,
                   title: str,
                   icon: str | None = None,
                   color: str | None = "red",
                   message: str | None = None,
                   error: Exception | None = None,
                   buttons: bool = True,
                   log: bool = True) -> None:
        # ToDo: implement favicon for error pages
        if self.sub_page_app.debug:
            title = f"(Debug Mode) - {title}"
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
            if error is not None and self.sub_page_app.debug:
                stack_trace = traceback.format_exc()
                ui.code(stack_trace)
                log_msg += f"\n{stack_trace}"
            if self.sub_page_app.debug:
                with ui.grid(columns=2):
                    ui.label("Router:")
                    ui.link(self.__class__.__name__, target=self.prefix)

                    ui.label("Parent Router:")
                    if self.parent_router is not None:
                        ui.link(self.parent_router.__class__.__name__, target=self.parent_router.prefix)
                    else:
                        ui.label("None")

                    ui.label("Sub Pages:")
                    with ui.row():
                        for path, kwargs in self.subpages.items():
                            ui.link(kwargs["title"], target=path)

                    ui.label("Included SubPageRouters:")
                    with ui.row():
                        for router in self.subpage_router:
                            ui.link(router.__class__.__name__, target=router.prefix)
            if buttons:
                with ui.row().classes("mt-4"):
                    ui.button("Go Home", icon="home", on_click=lambda: ui.navigate.to("/")).props("outline")
                    ui.button("Go Back", icon="arrow_back", on_click=ui.navigate.back).props("outline")
        if log:
            logger.error(log_msg)


class SubPageApp(APIRouter, SubPageRouter):
    def __init__(self,
                 debug: bool = False,
                 prefix: str = "",
                 **kwargs):
        APIRouter.__init__(self,
                           prefix=prefix,
                           **kwargs)
        SubPageRouter.__init__(self,
                               prefix=prefix)

        self.debug: bool = debug
        self.page("/{_:path}")(self.root)

