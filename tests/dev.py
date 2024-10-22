import uvicorn
from fastapi import FastAPI
from starlette.applications import Starlette

from nicegui_admin.admin import Admin
from nicegui_admin.layouts.nav_top import NavTopLayout
from nicegui_admin.views.base import ParameterMode
from nicegui_admin.views.custom import CustomView
from nicegui_admin.views.get_set import GetSetView

app = Starlette()

api = FastAPI()


@api.get("/")
async def read_root(qwe: int, list_str: list[str]):
    return {"Hello": "World"}


app.mount("/api", api)


class MyLayout(NavTopLayout):
    ...


class MyGetSetView1(GetSetView):
    name = "Test"
    path = "test/{action}"


class MyCustomView1(CustomView):
    path = "my-custom-view-1/{action}/{int_param1}/{str_param2:_}"
    # parameter_mode = ParameterMode.ALLOW_EXTRA

    # async def render(self, event: Optional[EventArguments] = None, action: str = "", int_param1: int = "123", str_param2: str = "qwe"):
    #     ui.label(f"View '{self.__class__.__name__}' got: {action=}, {int_param1=}, {str_param2=}").classes("text-2xl")


class MyCustomView2(CustomView):
    ...
    # async def render(self, event: Optional[EventArguments] = None, action: str = "", int_param1: int = "123", str_param2: str = "qwe"):
    #     ui.label(f"View '{self.__class__.__name__}' got: {action=}, {int_param1=}, {str_param2=}").classes("text-2xl")


class MyAdmin(Admin):
    ...


if __name__ == "__main__":
    # ui.run(native=True)
    uvicorn.run(
        MyAdmin(
            base_app=app,
            layout=MyLayout,
            views=[MyGetSetView1, MyCustomView1, MyCustomView2]
        ),
        host="0.0.0.0",
        port=8000,
        factory=True
    )

# http://localhost:8000/admin/my-view-1/asd?int_param1=456&str_param2=asd
