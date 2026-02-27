import json
import random
import string

from nicegui import ui, app
from sqlmodel import Field, SQLModel

from nicegui_admin.contrib.sqlmodel.admin import SqlModelAdmin
from nicegui_admin.contrib.sqlmodel.view import SqlModelCrudView


class MyAdmin(SqlModelAdmin):
    async def builder(self):
        with (ui.header().classes("items-center bg-blue-100")):
            for path, values in self.sub_pages.items():
                button = ui.button(text=values["title"],
                                   icon=values["icon"])
                button.props("flat")
                button.target = path
                button.on_click(lambda e: ui.navigate.to(f"{e.sender.target}?qwe={''.join(random.choices(string.ascii_letters + string.digits, k=10))}"))
            ui.button("Invalid", on_click=lambda: ui.navigate.to("/invalid")).props("flat")
        await super().builder()


admin = MyAdmin(debug=True)


class MyModel1(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    qwe: str = Field(index=True)


@admin.view(model=MyModel1, fields=["id", "qwe"])
class MyView1(SqlModelCrudView):
    ...


class MyModel2(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    asd: str = Field(index=True)


test2_view = SqlModelCrudView(model=MyModel2, fields=["id", "asd"])
admin.add_view(test2_view)


@admin.sub_page("/")
def home_page():
    ui.label("Home")


@admin.sub_page("/test")
def test(qwe: str = None):
    ui.label("Test")
    ui.label(f"qwe: {qwe}")


@admin.sub_page("/sync_error")
def sync_error_page():
    raise RuntimeError("Synchronous error")


@admin.sub_page("/async_error", title="Async Error")
async def async_error_page():
    raise RuntimeError("Asynchronous error")


@test2_view.sub_page("/")
async def index() -> None:
    await test2_view.create({"asd": "".join(random.choices(string.ascii_letters + string.digits, k=10))})
    result = await test2_view.list()
    for i, item in enumerate(result):
        item_json = json.dumps(item, indent=4)
        ui.label(f"Item {i}:\n{item_json}")


app.include_router(admin)

if __name__ in {"__main__", "__mp_main__"}:
    SQLModel.metadata.create_all(admin.engine)
    ui.run(port=8000, show=False, fastapi_docs=True)
