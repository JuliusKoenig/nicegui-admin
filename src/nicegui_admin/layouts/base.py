from typing import TYPE_CHECKING, Optional, Union, Any
from urllib.parse import urlparse
from urllib.parse import parse_qs

from nicegui import ui, Client
from nicegui.events import EventArguments
from starlette.requests import Request

from nicegui_admin.loader_dialog import LoaderDialog
from nicegui_admin.render_object import RenderObject, render_method

if TYPE_CHECKING:
    from nicegui_admin.admin import Admin
    from nicegui_admin.views.base import BaseView


class BaseLayout(RenderObject):
    render_order = ["loader"]

    # --- internal methods ---

    def __init__(self,
                 admin: "Admin",
                 request: Request,
                 client: Client):
        super().__init__()

        self._admin: "Admin" = admin
        self._request: Request = request
        self._client: Client = client
        self._current_url: str = request.url.path + ("?" + request.url.query if request.url.query else "")
        self._current_event: Optional[EventArguments] = None
        self._views: list[BaseView] = []
        self._current_view: Optional[BaseView] = None

        # add views
        for view in self.admin.views:
            self._views.append(view(layout=self))

        self.loader: Union[None, LoaderDialog, Any] = None

    def __str__(self):
        return f"{self.__class__.__name__}"

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
    def current_event(self) -> Optional[EventArguments]:
        return self._current_event

    @property
    def views(self) -> tuple["BaseView", ...]:
        return tuple(self._views)

    @property
    def current_view(self) -> Optional["BaseView"]:
        return self._current_view

    async def render_frame(self) -> Union[ui.element, Any]:
        frame_element = ui.element()
        frame_element.classes("w-full h-full")
        return frame_element

    async def render(self, *tag: str, strict: bool = False, skip_rendered: bool = True) -> None:
        await super().render(*tag, strict=strict, skip_rendered=skip_rendered)

        # close loader
        await self.loader("close")

    # --- user methods ---

    # async def render(self):
    #     # render loader
    #     await self.render_loader()
    #
    #     # open loader
    #     await self.loader("open", f"Loading layout {self} ...")
    #
    #     # render layout frame
    #     await self.render_layout_frame()

    # # render header
    # if self.header is not None:
    #     await self.loader("log", f"Loading header for layout {self} ...")
    #     with self.header:
    #         # render header content
    #         await self.header_content()
    #
    # # render right drawer
    # if self.right_drawer is not None:
    #     await self.loader("log", f"Loading right drawer for layout {self} ...")
    #     with self.right_drawer:
    #         # render right drawer content
    #         await self.right_drawer_content()
    #
    # # render left drawer
    # if self.left_drawer is not None:
    #     await self.loader("log", f"Loading left drawer for layout {self} ...")
    #     with self.left_drawer:
    #         # render left drawer content
    #         await self.left_drawer_content()
    #
    # # render footer
    # if self.footer is not None:
    #     await self.loader("log", f"Loading footer for layout {self} ...")
    #     with self.footer:
    #         # render footer content
    #         await self.footer_content()

    # # ToDo: remove this
    # await asyncio.sleep(1)
    #
    # # close loader
    # await self.loader("close")

    @render_method("loader", top_level=True)
    async def render_loader(self) -> None:
        self.loader = LoaderDialog(layout=self)
        await self.loader.render()

    def get_view_by_url(self, url: str) -> Optional["BaseView"]:
        if type(url) is not str:
            raise ValueError(f"Invalid url: {url}")
        found_view = None
        for view in self.views:
            if url.startswith(view.url):
                found_view = view
        return found_view

    def open_view(self, url: Optional[str] = None):
        async def open_view(event):
            # set current url
            if url is not None:
                self._current_url = url

            # set current event
            self._current_event = event

            # get view
            view = self.get_view_by_url(url=self.current_url)
            if view is None:
                # ToDo implement a 404 page
                print(f"404: {url}")
                return

            # open loader
            await self.loader("open", f"Open view '{view.name}' ...")

            # clear the frame element
            self.frame_element.clear()

            # set current view
            self._current_view = view

            # add the url to the browser history if it's not already there
            await ui.run_javascript(f"""if (window.location.pathname + window.location.search !== "{self.current_url}") {{
            history.pushState({{page: "{self.current_url}"}}, "", "{self.current_url}");
            }}""")

            # parse the url
            url_parsed = urlparse(self.current_url)

            # get path parameters values
            path_parameters_values = []
            for sub_path in url_parsed.path[len(view.url):].split("/"):
                if sub_path:
                    path_parameters_values.append(sub_path)

            # get query parameters
            query_params = parse_qs(url_parsed.query)

            # validate parameters for the view
            await view.open(path_parameters_values=path_parameters_values, query_params=query_params)

            # close loader
            await self.loader("close")

        return open_view
