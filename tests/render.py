import asyncio
from types import MappingProxyType
from typing import Literal

RENDER_METHOD_MODES = Literal["override", "prepend", "append"]

RENDER_METHODS_BUILD: dict[str, list[tuple[str, RENDER_METHOD_MODES]]] = {}


def render_method(*tags: str, mode: RENDER_METHOD_MODES = "append"):
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
    async def render(self, *tag: str):
        render_tags = list(tag or self._render_methods.keys())
        for tag in render_tags:
            for method in self._render_methods[tag]:
                if asyncio.iscoroutinefunction(method):
                    await method(self)
                else:
                    method(self)


class Parent(RenderObject):
    @render_method("topic")
    async def topic_parent(self):
        print("topic parent")


class Child(Parent):
    @render_method("topic")
    async def topic_child(self):
        print("topic child")

    @render_method("body")
    async def body_child(self):
        print("body child")


child = Child()

if __name__ == "__main__":
    asyncio.run(child.render("topic"))
    print()
