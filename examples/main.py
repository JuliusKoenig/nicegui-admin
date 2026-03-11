from nicegui import ui
from pydantic import BaseModel, Field as PydanticField
from sqlalchemy import String, Column
from sqlmodel import Field, SQLModel

from nicegui_admin.contrib.sqlmodel.admin import SqlModelAdmin
from nicegui_admin.contrib.sqlmodel.view import SqlModelCrudView


class MyAdmin(SqlModelAdmin):
    pass


admin = MyAdmin(debug=True)

class Test(BaseModel):
    asd: str = PydanticField(asd=123)


class MyModel(SQLModel, table=True):
    id: int | None = Field(default=None,
                           primary_key=True,
                           description="ID of the model",
                           schema_extra={"json_schema_extra": {"help_text": "Help -> ID of the model"}})
    name: str = Field(primary_key=True,
                      description="Name of the model")
    boolean_attr1: bool = Field(description="Boolean attribute 1")
    boolean_attr2: bool = Field(default=False,
                                description="Boolean attribute 2")
    integer_attr1: int = Field(description="Integer attribute 1")
    integer_attr2: int = Field(default=0,
                               description="Integer attribute 2")
    float_attr1: float = Field(description="Float attribute 1")
    float_attr2: float = Field(default=0.0,
                               description="Float attribute 2")
    string_attr1: str = Field(description="String attribute 1", max_length=10)
    string_attr2: str = Field(default="",
                              description="String attribute 2")


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
