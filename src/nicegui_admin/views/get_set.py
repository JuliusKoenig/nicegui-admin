from enum import Enum

from nicegui import ui

from nicegui_admin.views.base import BaseViewMeta, BaseView


class GetSetViewMeta(BaseViewMeta):
    def __new__(mcs, name, bases, namespace, **kwargs):
        # create cls
        cls = super().__new__(mcs, name, bases, namespace, **kwargs)

        return cls

    @classmethod
    def get_normalized_view_path_and_path_parameters(mcs, view_path: str) -> tuple[str, dict[str, bool]]:
        if not view_path.endswith("/{action}") or view_path.endswith("/{action}/"):
            view_path += "/{action}"
        return super().get_normalized_view_path_and_path_parameters(view_path=view_path)


class GetSetView(BaseView, metaclass=GetSetViewMeta):
    class Actions(Enum):
        GET = "get"
        SET = "set"

    async def render(self, action: Actions, *args, **kwargs):
        ui.label(f"{self}").classes("text-2xl")
        ui.label(f"Default render method")
        ui.label(f"{action=}").classes("text-lg")
        ui.label(f"{args=}").classes("text-lg")
        ui.label(f"{kwargs=}").classes("text-lg")
