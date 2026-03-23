import random
import string
import uuid
from ipaddress import IPv4Address, IPv6Address

from nicegui import ui
from sqlalchemy import String, Column
from sqlalchemy_utils import IPAddressType
from sqlmodel import Field, SQLModel

from nicegui_admin.contrib.sqlmodel.admin import SqlModelAdmin
from nicegui_admin.contrib.sqlmodel.view import SqlModelCrudView


class MyAdmin(SqlModelAdmin):
    pass


admin = MyAdmin(debug=True,
                engine="mysql+pymysql://test:test@localhost/test")


class MyModel(SQLModel, table=True):
    id: int | None = Field(default_factory=lambda: random.randint(1, 1000),
                           primary_key=True,
                           description="ID of the model")
    name: str = Field(default_factory=lambda: "".join(random.choices(string.ascii_letters, k=10)),
                      primary_key=True,
                      description="Name of the model",
                      min_length=3,
                      max_length=10,
                      schema_extra={'pattern': r'^[A-Za-z0-9\- ]+$'})
    boolean_attr1: bool = Field(description="Boolean attribute 1")
    boolean_attr2: bool = Field(default=False,
                                description="Boolean attribute 2")
    integer_attr1: int = Field(description="Integer attribute 1")
    integer_attr2: int = Field(default=0,
                               description="Integer attribute 2")
    float_attr1: float = Field(description="Float attribute 1")
    float_attr2: float = Field(default=0.0,
                               description="Float attribute 2")
    string_attr1: str = Field(description="String attribute 1")
    string_attr2: str = Field(default="",
                              description="String attribute 2")
    uuid_attr1: uuid.UUID = Field(description="UUID attribute 1")
    uuid_attr2: uuid.UUID = Field(default_factory=uuid.uuid4,
                                  description="UUID attribute 2")
    ip_v4_address_attr1: IPv4Address = Field(description="IP address attribute 1",
                                             sa_type=IPAddressType)
    ip_v4_address_attr2: IPv4Address = Field(default=IPv4Address("127.0.0.1"),
                                             description="IP address attribute 2",
                                             sa_type=IPAddressType)
    ip_v6_address_attr1: IPv6Address = Field(description="IP address attribute 1",
                                             sa_type=IPAddressType)
    ip_v6_address_attr2: IPv6Address = Field(default=IPv6Address("::1"),
                                             description="IP address attribute 2",
                                             sa_type=IPAddressType)


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
                                        "string_attr2",
                                        "uuid_attr1",
                                        "uuid_attr2",
                                        "ip_v4_address_attr1",
                                        "ip_v4_address_attr2",
                                        "ip_v6_address_attr1",
                                        "ip_v6_address_attr2"]))

# app.include_router(admin) # ToDo: check if it possible to act as a API Router

if __name__ in {"__main__", "__mp_main__"}:
    SQLModel.metadata.create_all(admin.engine)

    ui.run(port=8000, show=False, fastapi_docs=True, prod_js=False)
