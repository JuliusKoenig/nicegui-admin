import asyncio
import time
from dataclasses import dataclass, field, fields
from typing import Optional, TypeVar, Callable

from fastapi_utils.tasks import repeat_every

from nicegui import ui, app


def recursive_event(func):
    func_name = func.__name__

    async def wrapper(self, *args, **kwargs):
        result = await func(self, *args, **kwargs)
        for child in self.children.values():
            child_func = getattr(child, func_name)
            await child_func(*args, **kwargs)
        return result

    return wrapper


T = TypeVar("T", bound="NiceguiAdminObject")


@dataclass()
class NiceguiAdminObject:
    name: str | None = field(default=None)
    parent: Optional["NiceguiAdminObject"] = field(default=None,
                                                   repr=False,
                                                   metadata={"private": True})
    _init: bool = field(default=False,
                        init=False,
                        repr=False)
    _children: list["NiceguiAdminObject"] = field(default_factory=list,
                                                  init=False,
                                                  repr=False)
    _last_loop_time: float | None = field(default=None,
                                          init=False,
                                          repr=False)
    _loop_delay: float = field(default=1,
                               init=False,
                               repr=False)

    def __post_init__(self):
        if self.name is None:
            self.name = self.__class__.__name__
        if self.parent:
            self.parent.add_child(self)
        else:
            # register startup and shutdown handlers only for root objects
            app.on_startup(self.on_startup)
            app.on_shutdown(self.on_shutdown)

            @app.on_startup
            @repeat_every(seconds=0.001)
            async def loop() -> None:
                current_time = time.perf_counter()
                if self._last_loop_time is not None:
                    delta = current_time - self._last_loop_time
                    if delta < self._loop_delay:
                        await asyncio.sleep(self._loop_delay - delta)
                        return
                await self.on_server_loop()
                self._last_loop_time = current_time

            app.on_connect(self.on_connect)
            app.on_disconnect(self.on_disconnect)

        self._init = True

    def __setattr__(self,
                    key,
                    value):
        if self._init:
            _field = None
            for f in fields(self):
                if f.name == key:
                    _field = f
                    break
            if _field is not None:
                is_private = _field.metadata.get("private", False)
                if is_private:
                    raise AttributeError(f"{key} is a private field and cannot be set directly")
        super().__setattr__(key, value)

    @property
    def children(self) -> dict[str, "NiceguiAdminObject"]:
        children = {}
        for child in self._children:
            children[child.name] = child
        return children

    def child(self,
              **kwargs) -> Callable[[T | type[T]], T]:
        def decorator(obj: T | type[T]) -> T:
            return self.add_child(obj=obj,
                                  **kwargs)

        return decorator

    def add_child(self,
                  obj: T | type[T],
                  **kwargs) -> T:
        if type(obj) is type:
            return obj(parent=self,
                       **kwargs)

        if obj in self._children:
            raise ValueError(f"{obj} is already a child of {self}")
        self._children.append(obj)
        return obj

    def get_child_by_name(self,
                          name: str) -> T | None:
        if name not in self.children:
            return None
        return self.children[name]

    def get_child_by_type(self,
                          t: type[T]) -> list[T]:
        result = []
        for name, child in self.children.items():
            child_type = type(child)
            if issubclass(child_type, t):
                result.append(child)
        return result

    @recursive_event
    async def on_startup(self):
        print(f"Starting {self.name}")

    @recursive_event
    async def on_shutdown(self):
        print(f"Shutting down {self.name}")

    @recursive_event
    async def on_server_loop(self):
        print(f"Server Looping {self.name}")

    @recursive_event
    async def on_connect(self):
        await ui.context.client.connected()

        # ui.timer(1, self.on_client_loop)
        print(f"Connected to {self.name}")

    @recursive_event
    async def on_client_loop(self):
        print(f"Client Looping {self.name}")

    @recursive_event
    async def on_disconnect(self):
        print(f"Disconnected to {self.name}")


@dataclass()
class NiceguiAdmin(NiceguiAdminObject):
    ...


@dataclass()
class NiceguiAdminView(NiceguiAdminObject):
    ...


admin = NiceguiAdmin()


@admin.child(name="Test")
class MyView(NiceguiAdminView):
    ...


@ui.page("/")
async def root():
    ui.label("Hello World")


if __name__ in {"__main__", "__mp_main__"}:
    views = admin.get_child_by_type(NiceguiAdminView)
    ui.run(host="127.0.0.1",
           port=8000,
           show=False)
