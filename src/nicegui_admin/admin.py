import inspect
import logging
from typing import Optional, Union, Any

from fastapi import FastAPI
from fastapi.params import Param
from fastapi.dependencies.utils import ModelField, analyze_param
from nicegui import app, ui, APIRouter, Client
from nicegui.events import EventArguments
from starlette.applications import Starlette
from starlette.requests import Request

from nicegui_admin.helpers import normalize_name, validate_name, normalize_path, validate_path
from nicegui_admin.layouts.base import BaseLayout
from nicegui_admin.layouts.nav_top import NavTopLayout
from nicegui_admin.views.base import BaseView

logger = logging.getLogger(__name__)


class Admin:
    # --- internal methods ---

    def __init__(self,
                 base_path: Optional[str] = None,
                 storage_secret: Optional[str] = None,
                 layout: Optional[type[BaseLayout]] = None,
                 base_app: Union[None, Starlette, FastAPI] = None,
                 views: Optional[list[type[BaseView]]] = None):
        # set base path
        if base_path is None:
            base_path = "/admin"
        self._base_path: str = base_path

        # set storage secret
        self._storage_secret: Optional[str] = storage_secret

        # set layout
        if layout is None:
            layout = NavTopLayout
        self._layout: type[BaseLayout] = layout

        # set base app
        if base_app is None:
            base_app = Starlette()
        self._base_app: Union[Starlette, FastAPI] = base_app

        # create router
        self._router: APIRouter = APIRouter()

        # define views
        self._views: list[tuple[type[BaseView], list[ModelField], Optional[str]]] = []  # (view, render_model_fields, render_require_event_var)

        # add views
        if views is not None:
            for view in views:
                self.add_view(view)

    def __call__(self) -> Union[Starlette, FastAPI]:
        # check if layout is set
        if not issubclass(self.layout, BaseLayout):
            raise ValueError(f"Layout must be a subclass of {BaseLayout.__name__}")

        # add routes
        self.router.page(path="/")(self._render)
        self.router.page(path="/{_:path}")(self._render)

        # include router
        app.include_router(self.router)

        # mount
        ui.run_with(
            app=self.base_app,
            mount_path=self.base_path,
            storage_secret=self.storage_secret,
        )

        return self.base_app

    async def _render(self, request: Request, client: Client):
        await client.connected()

        # call before connect
        result = await self.before_render(request=request, client=client)
        layout_args = []
        layout_kwargs = {}
        if type(result) is tuple:
            if len(result) > 0:
                # noinspection PyTypeChecker
                layout_args = list(result[0])
                layout_kwargs = {}
            if len(result) > 1:
                # noinspection PyTypeChecker
                layout_kwargs = dict(result[1])
            if len(result) > 2:
                raise ValueError("Invalid result length")
        elif result is not None:
            layout_args = [result]

        # create layout
        layout = self.layout(admin=self, request=request, client=client, *layout_args, **layout_kwargs)

        # call after connect
        await self.after_render(request=request, client=client, layout=layout)

        # render layout
        await layout.render()

        # open view
        await layout.open_view()(None)

    # --- properties ---

    @property
    def base_path(self) -> str:
        return self._base_path

    @property
    def storage_secret(self) -> Optional[str]:
        return self._storage_secret

    @property
    def layout(self) -> type[BaseLayout]:
        return self._layout

    @property
    def base_app(self) -> Union[Starlette, FastAPI]:
        if self._base_app is None:
            raise ValueError("Base app is not set")
        return self._base_app

    @property
    def router(self) -> APIRouter:
        if self._router is None:
            raise ValueError("Router is not set")
        return self._router

    @property
    def views(self) -> tuple[type[BaseView], ...]:
        views = []
        for view, _, _ in self._views:
            views.append(view)
        return tuple(views)

    # --- user methods ---

    async def before_render(self, request: Request, client: Client) -> Union[None, Any, tuple[tuple[Any, ...], dict[str, Any]]]:
        ...

    async def after_render(self, request: Request, client: Client, layout: BaseLayout) -> None:
        ...

    def add_view(self, view: type[BaseView]):
        # check if view already exists
        if view in self.views:
            raise ValueError(f"View '{view.__name__}' already added.")

        # if name is not set, use the class name
        if view.name is None:
            view.name = normalize_name(view.__name__)

        # validate name
        if not validate_name(view.name):
            raise ValueError(f"View '{view.__name__}' name '{view.name}' is invalid.")

        # if path is not set, use the normalized name
        if view.path is None:
            view.path = normalize_path(view.name)

        # validate path
        if not validate_path(view.path):
            raise ValueError(f"View '{view.__name__}' path '{view.path}' is invalid.")

        # check if path already exists
        for existing_view in self.views:
            if existing_view.path == view.path:
                raise ValueError(f"View with path '{view.path}' already exists")

        # get pydantic model fields for render method
        render_require_event_var = None
        render_model_fields: list[ModelField] = []
        for param_name, param in inspect.signature(view.render).parameters.items():
            # skip self parameter
            if param_name == "self":
                continue

            # raise error if EventArguments is not Optional
            if param.annotation == EventArguments:
                raise AttributeError(f"Parameter '{param_name}' for '{view.__name__}.{view.render.__name__}' with type '{param.annotation}' must be Optional.")

            # set the require event variable and continue
            if param.annotation == Optional[EventArguments]:
                if render_require_event_var is not None:
                    raise AttributeError(f"Only one EventArguments parameter is allowed for '{view.__name__}.{view.render.__name__}'.")
                render_require_event_var = param_name
                continue

            # get the field for the parameter
            param_details = analyze_param(
                param_name=param_name,
                annotation=param.annotation,
                value=param.default,
                is_path_param=False,
            )
            field = param_details.field

            # check if the field is a Param
            if not isinstance(field.field_info, Param):
                raise AttributeError(f"Parameter '{param_name}' for '{view.__name__}.{view.render.__name__}' with type '{param.annotation}' is not supported.")

            # add the field to the list of fields
            render_model_fields.append(field)

        # add view
        self._views.append((view, render_model_fields, render_require_event_var))
