from nicegui import ui, app, APIRouter

from pydantic import BaseModel as BaseModel, Field


class CrudModel(BaseModel):
    ...


class CrudRouter(APIRouter):
    def __init__(self,
                 *,
                 model: type[CrudModel],
                 **kwargs):
        super().__init__(**kwargs)

        self.model: type[CrudModel] = model

        self.page("/list")(self.crud_list)
        self.page("/add")(self.crud_add)
        self.page("/edit/{id:int}")(self.crud_edit)

    async def crud_list(self):
        c = ui.context.c
        return ui.label("crud_list")

    async def crud_add(self):
        return ui.label("crud_list")

    async def crud_edit(self):
        return ui.label("crud_list")


class MyModel(CrudModel):
    username: str = Field(..., min_length=3, title="Benutzername", description="Der Benutzername für den Benutzer.")
    password: str = Field(None, min_length=8, title="Passwort", description="Das Passwort für den Benutzer.")
    test: str | None = None


my_router = CrudRouter(model=MyModel)
app.include_router(my_router, prefix="/crud")


@ui.page("/")
async def index():
    return ui.label("Hello World!")


if __name__ in {"__main__", "__mp_main__"}:
    ui.run(port=8000, show=False)
