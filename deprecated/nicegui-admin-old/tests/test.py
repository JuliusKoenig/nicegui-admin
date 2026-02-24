from nicegui import ui

from types import GenericAlias
from typing import Optional, Any, Union



class RenderObj:
    def __init__(self):
        ...



@ui.page("/")
def page() -> None:
    ui.label("Hello, world!")


ui.run(show=False, port=8000)

