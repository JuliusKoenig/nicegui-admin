import asyncio
import logging
from abc import ABC
from collections.abc import Callable
from typing import TYPE_CHECKING, Optional, Literal, Any
from urllib.parse import urlparse
from urllib.parse import parse_qs

from nicegui import ui, background_tasks, Client
from nicegui.events import EventArguments
from starlette.requests import Request

if TYPE_CHECKING:
    from nicegui_admin.admin import Admin
    from nicegui_admin.views.base import BaseView

logger = logging.getLogger(__name__)


class BaseLayout(ABC):
    class ViewFrame(ui.element, component="view_frame.js"):
        ...

    # --- internal methods ---

    def __init__(self,
                 admin: "Admin",
                 request: Request,
                 client: Client,
                 *args: tuple[Any, ...],
                 **kwargs: dict[str, Any]):
        self._admin: "Admin" = admin
        self._request: Request = request
        self._client: Client = client
        self._current_url: str = request.url.path + ("?" + request.url.query if request.url.query else "")

        logger.debug(f"Loader creating loader for {self}")
        self._loader: Callable[[Literal["open", "log", "close"], Optional[str]], None] = self.get_loader()

        logger.debug(f"Loader creating header for {self}")
        self._header: Optional[ui.header] = self.get_header()

        logger.debug(f"Loader creating right drawer for {self}")
        self._right_drawer: Optional[ui.right_drawer] = self.get_right_drawer()

        logger.debug(f"Loader creating left drawer for {self}")
        self._left_drawer: Optional[ui.left_drawer] = self.get_left_drawer()

        logger.debug(f"Loader creating footer for {self}")
        self._footer: Optional[ui.footer] = self.get_footer()

        logger.debug(f"Loader creating view frame for {self}")
        self._view_frame: BaseLayout.ViewFrame = self.get_view_frame()

        self._views: list[BaseView] = []
        self.args: tuple[Any, ...] = args
        self.kwargs: dict[str, Any] = kwargs

        logger.debug(f"Layout {self} initialized")

    def __str__(self):
        return f"{self.__class__.__name__}"

    async def _open_view(self, view: "BaseView", event: Optional[EventArguments] = None) -> None:
        await self.loader("open", f"Open view '{view.name}' ...")

        with self.view_frame:
            # add the url to the browser history if it's not already there
            await ui.run_javascript(f"""if (window.location.pathname + window.location.search !== "{self.current_url}") {{
            history.pushState({{page: "{self.current_url}"}}, "", "{self.current_url}");
            }}""")

            # get query parameters
            query_params = parse_qs(urlparse(self.current_url).query)

            # render the view
            await view(event=event, query_params=query_params)

        await self.loader("close")

    # --- properties ---

    @property
    def admin(self) -> "Admin":
        return self._admin

    @property
    def request(self) -> Request:
        return self._request

    @property
    def client(self) -> Client:
        return self._client

    @property
    def current_url(self) -> str:
        return self._current_url

    @property
    def header(self) -> Optional[ui.header]:
        return self._header

    @property
    def right_drawer(self) -> Optional[ui.right_drawer]:
        return self._right_drawer

    @property
    def left_drawer(self) -> Optional[ui.left_drawer]:
        return self._left_drawer

    @property
    def footer(self) -> Optional[ui.footer]:
        return self._footer

    @property
    def view_frame(self) -> ViewFrame:
        return self._view_frame

    @property
    def views(self) -> tuple["BaseView", ...]:
        return tuple(self._views)

    # --- user methods ---

    async def render(self):
        # open loader
        await self.loader("open", f"Loading layout {self} ...")

        # # adding some navigation buttons to switch between the different pages
        # with ui.row():
        #     for view in self.admin.views.values():
        #         ui.button(text=view.name, on_click=self.open_view(url=view.url)).classes("w-32")

        # render header
        if self.header is not None:
            await self.loader("log", f"Loading header for layout {self} ...")
            with self.header:
                # render header content
                await self.header_content()

        # render right drawer
        if self.right_drawer is not None:
            await self.loader("log", f"Loading right drawer for layout {self} ...")
            with self.right_drawer:
                # render right drawer content
                await self.right_drawer_content()

        # render left drawer
        if self.left_drawer is not None:
            await self.loader("log", f"Loading left drawer for layout {self} ...")
            with self.left_drawer:
                # render left drawer content
                await self.left_drawer_content()

        # render footer
        if self.footer is not None:
            await self.loader("log", f"Loading footer for layout {self} ...")
            with self.footer:
                # render footer content
                await self.footer_content()

        # loading views
        for view, render_model_fields, render_require_event_var in self.admin._views:
            await self.loader("log", f"Loading view '{view.name}' for layout {self} ...")
            self._views.append(view(admin=self.admin,
                                    render_model_fields=render_model_fields,
                                    render_require_event_var=render_require_event_var))

        # close loader
        await self.loader("close")

    def get_view_by_url(self, url: str) -> Optional["BaseView"]:
        if type(url) is not str:
            raise ValueError(f"Invalid url: {url}")
        found_view = None
        for view in self.views:
            if url.startswith(view.url):
                found_view = view
        return found_view

    def get_loader(self) -> Callable[[Literal["open", "log", "close"], Optional[str]], None]:
        # create loader dialog
        with ui.dialog().props("persistent") as loader_dialog, ui.card(align_items="center"):
            ui.spinner(size="lg").classes("mt-8 text-2xl")
            loader_log = ui.label().classes("m-8 text-xl")

        @ui.refreshable
        def loader(command: [Literal["open", "log", "close"]], msg: Optional[str] = None) -> None:
            if command == "open":
                if not loader_dialog.value:
                    logger.debug(f"Opening loader dialog for {self}")
                    loader_dialog.open()
            elif command == "log":
                ...
            elif command == "close":
                if loader_dialog.value:
                    logger.debug(f"Closing loader dialog for {self}")
                    loader_dialog.close()
            else:
                raise ValueError(f"Invalid command: {command}")
            if msg is not None:
                logger.info(msg)
                loader_log.text = msg


        # initial refresh
        loader("close")

        return loader.refresh

    async def loader(self, command: Literal["open", "log", "close"], msg: Optional[str] = None) -> None:
        self._loader(command, msg)
        await asyncio.sleep(0.001)

    def get_header(self) -> Optional[ui.header]:
        return ui.header(elevated=True).style("background-color: #3874c8").classes("items-center justify-between")

    async def

    async def header_content(self) -> None:
        ui.label("HEADER")
        ui.button(on_click=lambda: self.right_drawer.toggle(), icon="menu").props("flat color=white")

    def get_right_drawer(self) -> Optional[ui.right_drawer]:
        return ui.right_drawer(fixed=False).style("background-color: #ebf1fa").props("bordered")

    async def right_drawer_content(self) -> None:
        ui.label("RIGHT DRAWER")

    def get_left_drawer(self) -> Optional[ui.left_drawer]:
        return ui.left_drawer(top_corner=True, bottom_corner=True).style("background-color: #d7e3f4")

    async def left_drawer_content(self) -> None:
        ui.label("LEFT DRAWER")

    def get_footer(self) -> Optional[ui.footer]:
        return ui.footer().style("background-color: #3874c8")

    async def footer_content(self) -> None:
        ui.label("FOOTER")

    def get_view_frame(self) -> ViewFrame:
        view_frame = self.ViewFrame()
        view_frame.classes("w-full p-4 bg-gray-100")
        return view_frame

    def open_view(self, url: Optional[str] = None):
        async def decorator(event):
            # set the view url
            if url is not None:
                self._current_url = url

            # get view
            view = self.get_view_by_url(url=self.current_url)
            if view is None:
                # ToDo implement a 404 page
                print(f"404: {url}")
                return

            # clear the content
            self.view_frame.clear()  # ToDo move to _render_view

            # render the view
            background_tasks.create(self._open_view(view=view, event=event))

        return decorator
