import asyncio
from typing import TYPE_CHECKING, Optional, Literal
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

    loader_dialog_class: type[LoaderDialog] = LoaderDialog

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

        # init loader dialog
        self._loader: LoaderDialog = self.loader_dialog_class(layout=self)

        # self._header: Optional[ui.header] = self.get_header()
        # self._right_drawer: Optional[ui.right_drawer] = self.get_right_drawer()
        # self._left_drawer: Optional[ui.left_drawer] = self.get_left_drawer()
        # self._footer: Optional[ui.footer] = self.get_footer()
        # self._view_frame: BaseLayout.ViewFrame = self.get_view_frame()

        # define elements
        # self._loader_dialog_element: Optional[ui.dialog] = None
        # self._loader_frame_element: Union[None, ui.element, Any] = None
        # self._loader_spinner_element: Optional[ui.spinner] = None
        # self._loader_log_element: Optional[ui.label] = None
        # self._loader_refreshable: Optional[Callable[[Literal["open", "log", "close"], Optional[str]], None]] = None

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

    # @property
    # def header(self) -> Optional[ui.header]:
    #     return self._header
    #
    # @property
    # def right_drawer(self) -> Optional[ui.right_drawer]:
    #     return self._right_drawer
    #
    # @property
    # def left_drawer(self) -> Optional[ui.left_drawer]:
    #     return self._left_drawer
    #
    # @property
    # def footer(self) -> Optional[ui.footer]:
    #     return self._footer
    #
    # @property
    # def view_frame(self) -> ViewFrame:
    #     return self._view_frame

    @property
    def views(self) -> tuple["BaseView", ...]:
        return tuple(self._views)

    @property
    def current_view(self) -> Optional["BaseView"]:
        return self._current_view

    @property
    def loader(self) -> LoaderDialog:
        return self._loader

    # @property
    # def loader_dialog_element(self) -> ui.dialog:
    #     if self._loader_dialog_element is None:
    #         raise ValueError("Loader dialog element not rendered")
    #     return self._loader_dialog_element
    #
    # @property
    # def loader_frame_element(self) -> Union[ui.element, Any]:
    #     if self._loader_frame_element is None:
    #         raise ValueError("Loader frame element not rendered")
    #     return self._loader_frame_element
    #
    # @property
    # def loader_spinner_element(self) -> ui.spinner:
    #     if self._loader_spinner_element is None:
    #         raise ValueError("Loader spinner element not rendered")
    #     return self._loader_spinner_element
    #
    # @property
    # def loader_log_element(self) -> ui.label:
    #     if self._loader_log_element is None:
    #         raise ValueError("Loader log element not rendered")
    #     return self._loader_log_element
    #
    # @property
    # def layout_frame_element(self) -> Union[ui.element, Any]:
    #     if self._layout_frame_element is None:
    #         raise ValueError("Layout frame not rendered")
    #     return self._layout_frame_element

    # @property
    # def custom_elements(self) -> MappingProxyType[str, ui.element]:
    #     return MappingProxyType(self._custom_elements)

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

    # @render_method("first")
    # def test1(self):
    #     print("test1")
    #
    # @render_method("second")
    # def test2(self):
    #     print("test2")

    @render_method("loader")
    async def render_loader(self) -> None:
        await self.loader.render()

    @render_method("header")
    async def render_header(self) -> None:
        await self.loader("log", f"Loading header for layout {self} ...")

    # async def render_layout_frame(self) -> None:
    #     self._layout_frame_element = ui.element().classes("w-full h-full bg-gray-100")



    # def add_custom_element(self, key: str, element: ui.element):
    #     if key in self._custom_elements:
    #         raise ValueError(f"Element {key} is already added")
    #     self._custom_elements[key] = element

    # def get_header(self) -> Optional[ui.header]:
    #     return ui.header(elevated=True).style("background-color: #3874c8").classes("items-center justify-between")
    #
    # async def header_content(self) -> None:
    #     with ui.row():
    #         ui.label("HEADER")
    #
    #         # adding some navigation buttons to switch between the different pages
    #         for view in self.views:
    #             ui.button(text=view.name, on_click=self.open_view(url=view.url)).classes("w-32")
    #
    #     ui.button(on_click=lambda: self.right_drawer.toggle(), icon="menu").props("flat color=white")
    #
    # def get_right_drawer(self) -> Optional[ui.right_drawer]:
    #     return ui.right_drawer(value=False, fixed=False).style("background-color: #ebf1fa").props("bordered")
    #
    # async def right_drawer_content(self) -> None:
    #     ui.label("RIGHT DRAWER")
    #
    # def get_left_drawer(self) -> Optional[ui.left_drawer]:
    #     return ui.left_drawer(value=False, top_corner=True, bottom_corner=True).style("background-color: #d7e3f4")
    #
    # async def left_drawer_content(self) -> None:
    #     ui.label("LEFT DRAWER")
    #
    # def get_footer(self) -> Optional[ui.footer]:
    #     return ui.footer().style("background-color: #3874c8")
    #
    # async def footer_content(self) -> None:
    #     ui.label("FOOTER")
    #
    # def get_view_frame(self) -> ViewFrame:
    #     view_frame = self.ViewFrame()
    #     view_frame.classes("w-full p-0 bg-gray-100")
    #     return view_frame

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
            view_args, view_kwargs, param_errors = await view.validate(path_parameters_values=path_parameters_values, query_params=query_params)

            if len(param_errors) > 0:
                raise AttributeError(f"Errors while validating parameters: {param_errors}")  # ToDo: improve error message

            # clear the content
            self.layout_frame_element.clear()

            # set current view
            self._current_view = view

            with self.layout_frame_element:
                # render the view
                await self.current_view.render(*view_args, **view_kwargs)

            await self.loader("close")

        return open_view
