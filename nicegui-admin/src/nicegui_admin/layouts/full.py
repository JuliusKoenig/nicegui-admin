from typing import TYPE_CHECKING, Union, Any

from nicegui import ui, Client
from starlette.requests import Request

if TYPE_CHECKING:
    from nicegui_admin.admin import Admin

from nicegui_admin.layouts.base import BaseLayout
from nicegui_admin.render_object import render_method


class FullLayout(BaseLayout):
    def __init__(self,
                 admin: "Admin",
                 request: Request,
                 client: Client):
        super().__init__(admin=admin,
                         request=request,
                         client=client)

        self.header: Union[None, ui.header, Any] = None
        self.left_drawer: Union[None, ui.left_drawer, Any] = None
        self.right_drawer: Union[None, ui.right_drawer, Any] = None
        self.footer: Union[None, ui.footer, Any] = None

    @render_method("header", top_level=True)
    async def render_header(self) -> None:
        await self.loader("log", f"Loading header for layout {self} ...")

        self.header = ui.header(elevated=True)
        self.header.style("background-color: #3874c8")
        self.header.classes("items-center justify-between")

    @render_method("left_drawer", top_level=True)
    async def render_left_drawer(self) -> None:
        await self.loader("log", f"Loading left drawer for layout {self} ...")

        self.left_drawer = ui.left_drawer(value=False)#, top_corner=True, bottom_corner=True)
        self.left_drawer.style("background-color: #d7e3f4")
        self.left_drawer.props("bordered")

    @render_method("right_drawer", top_level=True)
    async def render_right_drawer(self) -> None:
        await self.loader("log", f"Loading right drawer for layout {self} ...")

        self.right_drawer = ui.right_drawer(value=False)#, fixed=False)
        self.right_drawer.style("background-color: #ebf1fa")
        self.right_drawer.props("bordered")

    @render_method("footer", top_level=True)
    async def render_footer(self) -> None:
        await self.loader("log", f"Loading footer for layout {self} ...")

        self.footer = ui.footer()
        self.footer.style("background-color: #3874c8")
