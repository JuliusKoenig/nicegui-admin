from typing import Any

import uvicorn
from fastapi import FastAPI
from nicegui import ui
from pydantic import BaseModel, Field
from pydantic.fields import FieldInfo
from starlette.applications import Starlette

from nicegui_admin.admin import Admin
from nicegui_admin.converter import Converter, register_field_converter
from nicegui_admin.layouts.nav_top import NavTopLayout
from nicegui_admin.views.custom import CustomView
from nicegui_admin.views.get_set import GetSetView

app = Starlette()


class MyLayout(NavTopLayout):
    ...


class SubTestModel(BaseModel):
    sub_test_str: str = Field(default="qwe_sub",
                              title="Test string sub",
                              description="Test string sub description",
                              examples=["qwe_sub", "asd_sub"],
                              max_length=4)


class TestModel(BaseModel):
    # test_str: str = "qwe"
    test_str: str = Field(default="qwe",
                          title="Test string",
                          description="Test string description",
                          examples=["qwe", "asd"],
                          max_length=3)
    # test_int: int = Field(default=123, title="Test integer",
    #                       description="Test integer description",
    #                       examples=[123, 456],
    #                       ge=0,
    #                       le=1000)
    # test_float: float = Field(default=123.456,
    #                           title="Test float",
    #                           description="Test float description",
    #                           examples=[123.456, 456.789],
    #                           ge=0,
    #                           le=1000)
    # test_bool: bool = Field(default=True,
    #                         title="Test boolean",
    #                         description="Test boolean description",
    #                         examples=[True, False])
    # test_list: list = Field(default=["qwe", 123, 123.456, True],
    #                         title="Test list",
    #                         description="Test list description",
    #                         examples=[["qwe", 123, 123.456, True], ["asd", 456, 456.789, False]])
    # test_dict: dict = Field(default={"test_str": "qwe", "test_int": 123, "test_float": 123.456, "test_bool": True},
    #                         title="Test dict",
    #                         description="Test dict description",
    #                         examples=[{"test_str": "qwe", "test_int": 123, "test_float": 123.456, "test_bool": True},
    #                                   {"test_str": "asd", "test_int": 456, "test_float": 456.789, "test_bool": False}])

    test_sub: SubTestModel = Field(default=SubTestModel(), title="Test sub model", description="Test sub model description")


test = TestModel()


class MyConverter(Converter):
    ...
    # @register_field_converter(str)
    # def text_field_converter(self, field_name: str, field_info: FieldInfo):
    #     print()


class MyGetSetView1(GetSetView):
    name = "Test"
    path = "test/{action}"
    converter = MyConverter
    get_model = TestModel

    async def get(self) -> dict[str, Any]:
        data = test.model_dump()
        return data

    async def set(self, data: dict[str, Any]):
        global test
        test = TestModel(**data)


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


api = FastAPI()


@api.post("/")
async def read_root(qwe: TestModel):
    return {"Hello": "World"}


app.mount("/api", api)

# @ui.page("/")
# async def main(qwe: int = 123):
#     ui.button("Open admin")

# ui.run(show=False, port=8000)

if __name__ == "__main__":
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
