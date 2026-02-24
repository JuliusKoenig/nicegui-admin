import asyncio
from typing import TYPE_CHECKING, Union, Any, Optional, Callable, Literal

from nicegui import ui

from nicegui_admin.render_object import RenderObject, render_method

if TYPE_CHECKING:
    from nicegui_admin.layouts.base import BaseLayout


class LoaderDialog(RenderObject):
    def __init__(self, layout: "BaseLayout"):
        super().__init__()
        self._layout = layout
        self.refreshable: Optional[Callable[[Literal["open", "log", "close"], Optional[str]], None]] = None
        self.dialog_element: Union[None, ui.dialog, Any] = None
        self.spinner_element: Union[None, ui.spinner, Any] = None
        self.log_element: Union[None, ui.label, Any] = None

    async def __call__(self, command: Literal["open", "log", "close"], msg: Optional[str] = None) -> None:
        if self.refreshable is None:
            raise ValueError("Loader not rendered")
        self.refreshable(command, msg)
        await asyncio.sleep(0.001)

    @property
    def layout(self) -> "BaseLayout":
        return self._layout

    async def render_frame(self) -> Union[ui.element, Any]:
        self.dialog_element = ui.dialog().props("persistent")

        with self.dialog_element:
            return ui.card(align_items="center")

    async def render(self, *tag: str, strict: bool = False, skip_rendered: bool = True) -> None:
        await super().render(*tag, strict=strict, skip_rendered=skip_rendered)

        @ui.refreshable
        def loader(command: [Literal["open", "log", "close"]], msg: Optional[str] = None) -> None:
            if command == "open" or command == "log":
                if not self.dialog_element.value:
                    self.dialog_element.open()
            elif command == "close":
                if self.dialog_element.value:
                    self.dialog_element.close()
            else:
                raise ValueError(f"Invalid command: {command}")

            if msg is not None:
                self.log_element.text = msg

        # initial refresh
        loader("close")

        self.refreshable = loader.refresh

    @render_method()
    async def render_spinner(self) -> None:
        self.spinner_element = ui.spinner(size="lg")
        self.spinner_element.classes("mt-8 text-2xl")

    @render_method()
    async def render_loader_log(self) -> None:
        self.log_element = ui.label()
        self.log_element.classes("m-8 text-xl")
