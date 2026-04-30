from abc import ABCMeta
from dataclasses import dataclass, field, fields
from types import MappingProxyType
from typing import TYPE_CHECKING, Any, TypeVar, Callable, Literal, get_args

_EVENTS: dict[str, str] = {}


def event(name: str | None = None):
    def decorator(func: Callable[..., Any]):
        global _EVENTS
        nonlocal name

        method_name = func.__name__
        if name is None:
            name = method_name
        _EVENTS[method_name] = str(name)

        return func

    return decorator


class AdminTypeMeta(ABCMeta):
    def __new__(mcs, name, bases, namespace, **kwargs):
        events: dict[str, str] = {}

        # get events from bases
        for base in bases:
            if hasattr(base, "__events__"):
                for method_name, _name in base.__events__.items():
                    events[method_name] = _name

        # get global _EVENTS
        global _EVENTS
        for method_name, _name in _EVENTS.items():
            events[method_name] = _name
        _EVENTS.clear()

        namespace["__events__"] = events

        cls = super().__new__(mcs, name, bases, namespace, **kwargs)
        return cls


EVENT_TYPES = Literal["before", "after"]


class Event:
    def __init__(self,
                 admin_type: "AdminType",
                 name: str):
        self._admin_type: AdminType = admin_type
        self._name: str = name

    def __call__(self, *args, **kwargs):
        for _handler in self._admin_type._event_handlers[self._name]["before"]:
            _handler(*args, **kwargs)

        result = self.method(*args, **kwargs)

        for _handler in self._admin_type._event_handlers[self._name]["after"]:
            _handler(*args, **kwargs)

        return result

    @property
    def method(self):
        for method_name, name in getattr(self._admin_type, "__events__").items():
            if name == self._name:
                return object.__getattribute__(self._admin_type, method_name)
        raise RuntimeError(f"Event '{self._name}' not found.")

    def before(self):
        def decorator(func: Callable[..., Any]):
            self._admin_type.register_event_handler(self._name,
                                                    "before",
                                                    func)
            return func

        return decorator

    def after(self):
        def decorator(func: Callable[..., Any]):
            self._admin_type.register_event_handler(self._name,
                                                    "after",
                                                    func)
            return func

        return decorator


@dataclass
class AdminType(metaclass=AdminTypeMeta):
    name: str = field(default=None, metadata={"immutable": True})
    admin: "Admin" = field(default=None, init=False)
    _event_handlers: dict[str, dict[EVENT_TYPES, list[Callable]]] = field(default_factory=dict, init=False)
    _initialized: bool = field(default=False, init=False, metadata={"immutable": True})

    def __post_init__(self):
        if self.name is None:
            self.name = self.__class__.__name__
        for _, name in getattr(self, "__events__").items():
            self._event_handlers[name] = {_type: [] for _type in get_args(EVENT_TYPES)}
        self._initialized = True

    def __getattribute__(self, item):
        if item.startswith("_") or item in ["admin", "_initialized", "_event_handlers"]:
            return super().__getattribute__(item)
        for method_name, name in getattr(self, "__events__").items():
            if item != method_name:
                continue
            return Event(admin_type=self,
                         name=name)
        return super().__getattribute__(item)

    def __setattr__(self, key, value):
        if key == "_initialized":
            super().__setattr__(key, value)
        elif key == "admin":
            if self.admin is not None:
                raise RuntimeError("Admin is already set for this object.")
            super().__setattr__(key, value)
        else:
            immutable_field_names = []
            for _field in fields(self.__class__):
                if _field.metadata.get("immutable", False):
                    immutable_field_names.append(_field.name)
            if key in immutable_field_names and self._initialized:
                raise RuntimeError("Cannot set attributes after the Admin has been initialized.")
            super().__setattr__(key, value)

    @property
    def events(self) -> dict[str, Event]:
        events = {}
        for _, name in getattr(self, "__events__").items():
            events[name] = Event(admin_type=self, name=name)
        return events

    def register_event_handler(self,
                               event_name: str,
                               event_type: EVENT_TYPES,
                               handler: Callable[..., Any]):
        self._event_handlers[event_name][event_type].append(handler)


T = TypeVar("T", bound=AdminType)
ADMIN_TYPES = Literal["view", "extension"]


@dataclass
class Admin(AdminType):
    _objects: dict[ADMIN_TYPES, list[AdminType]] = field(default_factory=lambda: {_type: list() for _type in get_args(ADMIN_TYPES)}, init=False)

    @property
    def objects(self) -> dict[ADMIN_TYPES, dict[str, AdminType]]:
        objects = {}
        for _type, _objects in self._objects.items():
            objects[_type] = {}
            for _object in _objects:
                objects[_type][_object.name] = _object
        return objects

    def _add_object(self, cls: T, t: ADMIN_TYPES, **kwargs) -> T:
        if isinstance(cls, type):
            obj_instance = cls(**kwargs)
        else:
            obj_instance = cls

        # add to admin
        obj_instance.admin = self

        # add to objects
        if obj_instance.name in self._objects[t]:
            raise RuntimeError(f"{t.capitalize()} with name '{obj_instance.name}' already exists.")
        self._objects[t].append(obj_instance)

        return obj_instance

    @property
    def views(self) -> dict[str, AdminType]:
        return self.objects["view"]

    def view(self, **kwargs) -> Callable[[T], T]:
        def decorator(cls: T) -> T:
            return self.add_view(cls, **kwargs)

        return decorator

    @event()
    def add_view(self, cls: T, **kwargs) -> T:
        return self._add_object(cls, t="view", **kwargs)

    @property
    def extensions(self) -> dict[str, AdminType]:
        return self.objects["extension"]

    def extension(self, **kwargs) -> Callable[[T], T]:
        def decorator(cls: T) -> T:
            return self.add_extension(cls, **kwargs)

        return decorator

    @event()
    def add_extension(self, cls: T, **kwargs) -> T:
        return self._add_object(cls, t="extension", **kwargs)


@dataclass
class View(AdminType):
    @event()
    def list(self):
        print("list")

    @event()
    def detail(self):
        print("detail")

    @event()
    def create(self):
        print("create")

    @event()
    def edit(self):
        print("edit")

    @event()
    def delete(self):
        print("delete")


@dataclass
class Extension(AdminType):
    ...


@dataclass
class MyAdmin(Admin):
    ...


admin = MyAdmin()

@admin.events["add_view"].before()
def on_admin_init(*args, **kwargs):
    print("admin initialized")


@admin.view()
@dataclass
class MyView(View):
    ...


@admin.extension()
@dataclass
class MyExtension(Extension):
    ...





if __name__ == "__main__":
    print()
