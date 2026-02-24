import asyncio
from abc import ABC, ABCMeta, abstractmethod
from typing import Union, Any

from nicegui import ui

from types import MappingProxyType
from typing import Literal

RENDER_METHOD_MODES = Literal["override", "prepend", "append"]
RENDER_METHODS_BUILD: dict[str, list[tuple[str, RENDER_METHOD_MODES, bool]]] = {}


def render_method(*tags: str, mode: RENDER_METHOD_MODES = "append", top_level: bool = False):
    tags = list(tags)

    if len(tags) == 0:
        tags = ["default"]

    def decorator(func):
        global RENDER_METHODS_BUILD

        for tag in tags:
            if tag not in RENDER_METHODS_BUILD:
                RENDER_METHODS_BUILD[tag] = []
            RENDER_METHODS_BUILD[tag].append((func.__name__, mode, top_level))

        return func

    return decorator


class RenderObjectMeta(ABCMeta):
    def __new__(mcs, name, bases, namespace, **kwargs):
        # create cls
        cls = super().__new__(mcs, name, bases, namespace, **kwargs)

        # check if cls is abstract
        if ABC in bases:
            cls._abstract = True
            return cls

        render_methods_build: dict[str, list[tuple[str, RENDER_METHOD_MODES, bool]]] = {}

        # add all from base classes
        for base in bases:
            if not issubclass(base, RenderObject):
                continue

            for tag, build in getattr(base, "_render_methods_build", {}).items():
                if tag not in render_methods_build:
                    render_methods_build[tag] = []
                for method_name, mode, top_level in build:
                    # pop method_name if exists
                    for i, (m, _) in enumerate(render_methods_build[tag]):
                        if m == method_name:
                            render_methods_build[tag].pop(i)
                            break
                    render_methods_build[tag].append((method_name, mode, top_level))

        # add all from global RENDER_METHODS_BUILD
        global RENDER_METHODS_BUILD
        for tag, build in RENDER_METHODS_BUILD.items():
            if tag not in render_methods_build:
                render_methods_build[tag] = []
            for method_name, mode, top_level in build:
                # pop method_name if exists
                for i, (m, _, _) in enumerate(render_methods_build[tag]):
                    if m == method_name:
                        render_methods_build[tag].pop(i)
                        break
                render_methods_build[tag].append((method_name, mode, top_level))

        # set render method_name build list
        cls._render_methods_build = MappingProxyType(render_methods_build)

        # empty global RENDER_METHODS_BUILD
        RENDER_METHODS_BUILD = {}

        # build render list for each tag
        render_methods: dict[str, list[tuple[callable, bool]]] = {}
        for tag, build in render_methods_build.items():
            render_methods[tag] = []
            for method_name, mode, top_level in build:
                # get method
                method = getattr(cls, method_name)

                if mode == "override":
                    render_methods[tag] = [(method, top_level)]
                elif mode == "prepend":
                    render_methods[tag].insert(0, (method, top_level))
                elif mode == "append":
                    render_methods[tag].append((method, top_level))
                else:
                    raise ValueError(f"Invalid mode: {mode}")

        # set render methods
        cls._render_methods = MappingProxyType(render_methods)

        return cls


class RenderObject(ABC, metaclass=RenderObjectMeta):
    # user defined variables
    render_order: list[str] = ["default"]

    # internal variables
    _abstract: bool

    def __init__(self):
        self._rendered_tags: list[str] = []
        self.frame_element: Union[None, ui.element, Any] = None

    @abstractmethod
    async def render_frame(self) -> Union[ui.element, Any]:
        ...

    async def render(self, *tag: str, strict: bool = False, skip_rendered: bool = True) -> None:
        # render frame if not rendered
        if self.frame_element is None:
            frame_element = await self.render_frame()
            if frame_element is None:
                raise ValueError("Frame render method must return an element")
            self.frame_element = frame_element

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
            for method, top_level in self._render_methods[tag]:
                if asyncio.iscoroutinefunction(method):
                    if top_level:
                        await method(self)
                    else:
                        with self.frame_element:
                            await method(self)
                else:
                    if top_level:
                        method(self)
                    else:
                        with self.frame_element:
                            method(self)

            # add to rendered tags
            self._rendered_tags.append(tag)
