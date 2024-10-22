from nicegui import ui

from nicegui_admin.views.base import BaseView


class CustomView(BaseView):
    async def render(self, *args, **kwargs):
        ui.label(f"{self}").classes("text-2xl")
        ui.label(f"Default render method")
        ui.label(f"{args=}").classes("text-lg")
        ui.label(f"{kwargs=}").classes("text-lg")