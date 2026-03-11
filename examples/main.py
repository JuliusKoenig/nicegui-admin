from nicegui import ui
from sqlmodel import Field, SQLModel

from nicegui_admin.contrib.sqlmodel.admin import SqlModelAdmin
from nicegui_admin.contrib.sqlmodel.view import SqlModelCrudView


class MyAdmin(SqlModelAdmin):
    pass


admin = MyAdmin(debug=True)


class MyModel(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(primary_key=True)
    boolean_attr1: bool = Field()
    boolean_attr2: bool = Field(default=False)
    integer_attr1: int = Field()
    integer_attr2: int = Field(default=0)
    float_attr1: float = Field()
    float_attr2: float = Field(default=0.0)
    string_attr1: str = Field()
    string_attr2: str = Field(default="")


admin.add_view(SqlModelCrudView(title="Test",
                                path="/test",
                                model=MyModel,
                                fields=["id",
                                        "name",
                                        "boolean_attr1",
                                        "boolean_attr2",
                                        "integer_attr1",
                                        "integer_attr2",
                                        "float_attr1",
                                        "float_attr2",
                                        "string_attr1",
                                        "string_attr2"]))

# app.include_router(admin) # ToDo: check if it possible to act as a API Router

if __name__ in {"__main__", "__mp_main__"}:
    SQLModel.metadata.create_all(admin.engine)

    ui.run(port=8000, show=False, fastapi_docs=True, prod_js=False)
