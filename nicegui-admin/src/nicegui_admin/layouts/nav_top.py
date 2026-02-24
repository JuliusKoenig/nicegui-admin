from typing import TYPE_CHECKING, Union, Any

from nicegui import ui, Client
from starlette.requests import Request

if TYPE_CHECKING:
    from nicegui_admin.admin import Admin

from nicegui_admin.layouts.full import FullLayout
from nicegui_admin.render_object import render_method


class NavTopLayout(FullLayout):
    def __init__(self,
                 admin: "Admin",
                 request: Request,
                 client: Client):
        super().__init__(admin=admin,
                         request=request,
                         client=client)
    #
    #     self.header: Union[None, ui.header, Any] = None
    #     self.left_drawer: Union[None, ui.left_drawer, Any] = None
    #     self.right_drawer: Union[None, ui.right_drawer, Any] = None
    #     self.footer: Union[None, ui.footer, Any] = None

    async def render_header(self) -> None:
        await super().render_header()

        with self.header:
            ui.button(on_click=lambda: self.left_drawer.toggle(), icon="menu").props("flat color=white")

            with ui.row():
                ui.label("HEADER")

                # adding some navigation buttons to switch between the different pages # todo: rework this
                for view in self.views:
                    ui.button(text=view.name, on_click=self.open_view(url=view.url)).classes("w-32")

            ui.button(on_click=lambda: self.right_drawer.toggle(), icon="menu").props("flat color=white")

    # @render_method("header", top_level=True)
    # async def render_header(self) -> None:
    #     await self.loader("log", f"Loading header for layout {self} ...")
    #
    #     self.header = ui.header(elevated=True)
    #     self.header.style("background-color: #3874c8")
    #     self.header.classes("items-center justify-between")
    #
    #     with self.header:
    #         with ui.row():
    #             ui.label("HEADER")
    #
    #             # adding some navigation buttons to switch between the different pages # todo: rework this
    #             for view in self.views:
    #                 ui.button(text=view.name, on_click=self.open_view(url=view.url)).classes("w-32")
    #
    # @render_method("footer", top_level=True)
    # async def render_footer(self) -> None:
    #     await self.loader("log", f"Loading footer for layout {self} ...")
    #
    #     footer = ui.footer()
    #     footer.style("background-color: #3874c8")
    #
    #     with footer:
    #         ui.label("FOOTER")
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
