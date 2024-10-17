from typing import Optional

import uvicorn
from fastapi import FastAPI
from nicegui import ui
from nicegui.events import EventArguments
from starlette.applications import Starlette

from nicegui_admin.admin import Admin
from nicegui_admin.layouts.nav_top import NavTopLayout
from nicegui_admin.views.base import BaseView
from nicegui_admin.views.custom import CustomView

app = Starlette()

api = FastAPI()


@api.get("/")
async def read_root(qwe: int, list_str: list[str]):
    return {"Hello": "World"}


app.mount("/api", api)


class MyLayout(NavTopLayout):
    ...


class MyView1(CustomView):
    async def render(self, event: Optional[EventArguments] = None, int_param1: int = "123", str_param2: str = "qwe"):
        ui.label(f"View '{self.__class__.__name__}' got: {int_param1=}, {str_param2=}").classes("text-2xl")


class MyView2(CustomView):
    async def render(self, event: Optional[EventArguments] = None, int_param1: int = "123", str_param2: str = "qwe"):
        ui.label(f"View '{self.__class__.__name__}' got: {int_param1=}, {str_param2=}").classes("text-2xl")


class MyAdmin(Admin):
    ...


if __name__ == "__main__":
    # ui.run(native=True)
    uvicorn.run(
        MyAdmin(
            base_app=app,
            layout=MyLayout,
            views=[MyView1, MyView2]
        ),
        host="0.0.0.0",
        port=8000,
        factory=True
    )

# http://localhost:8000/admin/my-view-1/asd?int_param1=456&str_param2=asd
