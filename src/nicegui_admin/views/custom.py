from nicegui import ui

from nicegui_admin.views.base import BaseView


class CustomView(BaseView):
    # async def render(self, action: str = "", int_param1: int = "123", str_param2: str = "qwe", **kwargs):
    #     ui.label(f"View '{self.__class__.__name__}' got: {action=}, {int_param1=}, {str_param2=}").classes("text-2xl")

    async def render(self, *args, **kwargs):
        ui.label(f"{self}").classes("text-2xl")
        ui.label(f"Default render method")
        ui.label(f"{args=}").classes("text-lg")
        ui.label(f"{kwargs=}").classes("text-lg")