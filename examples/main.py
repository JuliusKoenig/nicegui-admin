import json
import random
import string

from nicegui import ui, app
from sqlmodel import Field, SQLModel

from niceguitools.admin.contrib.sqlmodel.admin import SqlModelAdmin
from niceguitools.admin.contrib.sqlmodel.view import SqlModelCrudView

admin = SqlModelAdmin()


class MyModel1(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    qwe: str = Field(index=True)


@admin.view(model=MyModel1)
class MyView1(SqlModelCrudView):
    ...


class MyModel2(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    asd: str = Field(index=True)


test2_view = SqlModelCrudView(model=MyModel2)
admin.add_view(test2_view)


@test2_view.page("/")
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
