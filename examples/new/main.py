from dataclasses import dataclass, field
from typing import Optional, TypeVar

from nicegui import ui, app

T = TypeVar("T", bound="NiceguiAdminObject")

@dataclass()
class NiceguiAdminObject:
    parent: Optional["NiceguiAdminObject"] = field(default=None)
    _children: list["NiceguiAdminObject"] = field(default_factory=list,
                                                  init=False,
                                                  repr=False)

    def __post_init__(self):
        if self.parent:
            self.parent.add_children(self)
        print("post init")

    async def on_startup(self) -> None:
        print("startup")

    async def on_shutdown(self) -> None:
        print("shutdown")

    def children(self):
        def decorator(object_type: T | type[T]) -> T:
            return self.add_children(object_type=object_type)
        return decorator

    def add_children(self,
                     object_type: T | type[T]) -> T:
        if type(object_type) is type:
            object_type = object_type(parent=self)
        else:
            if object_type in self._children:
                raise ValueError("Children already exists")
            self._children.append(object_type)
        return object_type


@dataclass()
class NiceguiAdmin(NiceguiAdminObject):
    ...


@dataclass()
class NiceguiAdminView(NiceguiAdminObject):
    ...


admin = NiceguiAdmin()


@admin.children()
class MyView(NiceguiAdminView):
    ...

@ui.page("/")
async def root():
    ui.label("Hello World")


if __name__ in {"__main__", "__mp_main__"}:
    ui.run(host="127.0.0.1",
           port=8000,
           show=False)
