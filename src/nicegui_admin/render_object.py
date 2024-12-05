import asyncio
from typing import Union, Any

from nicegui import ui

from types import MappingProxyType
from typing import Literal

RENDER_METHOD_MODES = Literal["override", "prepend", "append"]

RENDER_METHODS_BUILD: dict[str, list[tuple[str, RENDER_METHOD_MODES]]] = {}


def render_method(*tags: str, mode: RENDER_METHOD_MODES = "append"):
    tags = list(tags)

    if len(tags) == 0:
        tags = ["default"]

    def decorator(func):
        global RENDER_METHODS_BUILD

        for tag in tags:
            if tag not in RENDER_METHODS_BUILD:
                RENDER_METHODS_BUILD[tag] = []
            RENDER_METHODS_BUILD[tag].append((func.__name__, mode))

        return func

    return decorator


class RenderObjectMeta(type):
    def __new__(mcs, name, bases, namespace, **kwargs):
        cls = super().__new__(mcs, name, bases, namespace, **kwargs)

        render_methods_build: dict[str, list[tuple[str, RENDER_METHOD_MODES]]] = {}

        # add all from base classes
        for base in bases:
            if not issubclass(base, RenderObject):
                continue

            for tag, build in getattr(base, "_render_methods_build", {}).items():
                if tag not in render_methods_build:
                    render_methods_build[tag] = []
                for method_name, mode in build:
                    # pop method_name if exists
                    for i, (m, _) in enumerate(render_methods_build[tag]):
                        if m == method_name:
                            render_methods_build[tag].pop(i)
                            break
                    render_methods_build[tag].append((method_name, mode))

        # add all from global RENDER_METHODS_BUILD
        global RENDER_METHODS_BUILD
        for tag, build in RENDER_METHODS_BUILD.items():
            if tag not in render_methods_build:
                render_methods_build[tag] = []
            for method_name, mode in build:
                # pop method_name if exists
                for i, (m, _) in enumerate(render_methods_build[tag]):
                    if m == method_name:
                        render_methods_build[tag].pop(i)
                        break
                render_methods_build[tag].append((method_name, mode))

        # empty global RENDER_METHODS_BUILD
        RENDER_METHODS_BUILD = {}

        # set render method_name build list
        cls._render_methods_build = MappingProxyType(render_methods_build)

        # build render list for each tag
        render_methods: dict[str, list[callable]] = {}
        for tag, build in render_methods_build.items():
            render_methods[tag] = []
            for method_name, mode in build:
                # get method
                method = getattr(cls, method_name)

                if mode == "override":
                    render_methods[tag] = [method]
                elif mode == "prepend":
                    render_methods[tag].insert(0, method)
                elif mode == "append":
                    render_methods[tag].append(method)
                else:
                    raise ValueError(f"Invalid mode: {mode}")

        # set render methods
        cls._render_methods = MappingProxyType(render_methods)

        return cls


class RenderObject(metaclass=RenderObjectMeta):
    render_order: list[str] = ["default"]

    def __init__(self):
        self._rendered_tags: list[str] = []
        self._frame_element: Union[None, ui.element, Any] = None
        self._elements: dict[str, Union[ui.element, Any]] = {}

    def __getattr__(self, item):
        if not self.is_element(key=item):
            return super().__getattribute__(item)
        if item not in self._elements:
            raise AttributeError(f"Element '{item}' not found")
        return self._elements[item]

    def __setattr__(self, key, value):
        if not self.is_element(key=key, value=value):
            return super().__setattr__(key, value)
        if key in self._elements:
            raise ValueError(f"Element '{key}' already exists")
        self._elements[key] = value

    @property
    def frame_element(self) -> Union[ui.element, Any]:
        if self._frame_element is None:
            raise ValueError("Frame not rendered")
        return self._frame_element

    @classmethod
    def is_element(cls, key: str, value: Any = None) -> bool:
        if key.startswith("_"):
            return False
        if value is not None:
            if not isinstance(value, ui.element):
                return False
        if not key.endswith("_element"):
            return False
        return True

    async def render_frame(self) -> None:
        self._frame_element = ui.element()
        self.frame_element.classes("w-full h-full")

    async def render(self, *tag: str, strict: bool = False, skip_rendered: bool = True) -> None:
        # render frame if not rendered
        if self._frame_element is None:
            await self.render_frame()

        # get render tags
        render_tags = list(tag or self._render_methods.keys())

        # order render tags
        render_tags.sort(key=lambda x: self.render_order.index(x) if x in self.render_order else len(self.render_order))

        for tag in render_tags:
            # check if tag exists
            if tag not in self._render_methods:
                if strict:
                    raise ValueError(f"Tag '{tag}' not found")
                continue

            # skip if already rendered
            if skip_rendered and tag in self._rendered_tags:
                continue

            # render tag
            for method in self._render_methods[tag]:
                if asyncio.iscoroutinefunction(method):
                    with self.frame_element:
                        await method(self)
                else:
                    with self.frame_element:
                        method(self)

            # add to rendered tags
            self._rendered_tags.append(tag)
