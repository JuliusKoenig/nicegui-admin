import json
import random
import string

from nicegui import ui, app
from sqlmodel import Field, SQLModel

from nicegui_admin.contrib.sqlmodel.admin import SqlModelAdmin
from nicegui_admin.contrib.sqlmodel.view import SqlModelCrudView


class MyAdmin(SqlModelAdmin):
    pass


admin = MyAdmin(debug=True, prefix="/admin")


# class MyModel1(SQLModel, table=True):
#     id: int | None = Field(default=None, primary_key=True)
#     qwe: str = Field(index=True)
#
#
# @admin.view(model=MyModel1, fields=["id", "qwe"])
# class MyView1(SqlModelCrudView):
#     ...


class MyModel2(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(primary_key=True)
    asd: str = Field(index=True)


test2_view = SqlModelCrudView(model=MyModel2, fields=["id", "name", "asd"])
admin.add_view(test2_view)


# @admin.sub_page("/")
# def home_page():
#     ui.label("Home")
#
#
# @admin.sub_page("/test")
# def test(qwe: str = None):
#     ui.label("Test")
#     ui.label(f"qwe: {qwe}")
#
#
# @admin.sub_page("/sync_error")
# def sync_error_page():
#     raise RuntimeError("Synchronous error")
#
#
# @admin.sub_page("/async_error", title="Async Error")
# async def async_error_page():
#     raise RuntimeError("Asynchronous error")



# app.include_router(admin) # ToDo: check if it possible to act as a API Router

if __name__ in {"__main__", "__mp_main__"}:
    SQLModel.metadata.create_all(admin.engine)

    ui.run(port=8000, show=False, fastapi_docs=True, prod_js=False)
