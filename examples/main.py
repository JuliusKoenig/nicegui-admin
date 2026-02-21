from nicegui import ui, app

from niceguitools.crud.fields.text import TextField
from niceguitools.crud.model import CrudModel
from niceguitools.crud.field import Field
from niceguitools.crud.router import CrudRouter
from niceguitools.crud.views.list import ListView


class MyModel(CrudModel):
    implicit: str
    explicit: str = Field(None, min_length=8, title="Explizites Feld",
                          description="Ein explizites Feld mit Validierung", crud_field=TextField())
    not_on_list: str = Field(None, min_length=8, title="Nicht in ListView",
                             description="Ein Feld, das nicht in der ListView angezeigt wird", crud_field=TextField(hide=[ListView]))
    only_pydantic: str = Field(None, min_length=8, title="Nur Pydantic",
                               description="Ein Feld, das nur von Pydantic verarbeitet wird", crud_field=None)


my_router = CrudRouter(model=MyModel)
app.include_router(my_router, prefix="/crud")


@ui.page("/")
async def index():
    return ui.label("Hello World!")


@app.post("/test")
async def test(attr: MyModel) -> MyModel:
    return attr


if __name__ in {"__main__", "__mp_main__"}:
    ui.run(port=8000, show=False, fastapi_docs=True)
