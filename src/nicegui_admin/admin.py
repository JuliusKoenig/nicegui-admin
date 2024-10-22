import inspect
import logging
import re
import string
from typing import Optional, Union, Any

from fastapi import FastAPI
from fastapi.params import Param
from fastapi.dependencies.utils import ModelField, analyze_param
from nicegui import app, ui, APIRouter, Client
from starlette.applications import Starlette
from starlette.requests import Request

from nicegui_admin.layouts.base import BaseLayout
from nicegui_admin.layouts.nav_top import NavTopLayout
from nicegui_admin.views.base import BaseView, ParameterMode

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
        self._views: list[type[BaseView]] = []  # (view, render_signature, render_model_fields)

        # add views
        if views is not None:
            for view in views:
                self.add_view(view)

    def __str__(self):
        base_path = self.base_path
        return f"{self.__class__.__name__}({base_path=})"

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
        return tuple(self._views)

    # --- user methods ---

    async def before_render(self, request: Request, client: Client) -> Union[None, Any, tuple[tuple[Any, ...], dict[str, Any]]]:
        ...

    async def after_render(self, request: Request, client: Client, layout: BaseLayout) -> None:
        ...

    def add_view(self, view: type[BaseView]):
        # check if view is a subclass of BaseView
        if not issubclass(view, BaseView):
            raise ValueError(f"View must be a subclass of {BaseView.__name__}")

        # check if view already exists
        if view in self.views:
            raise ValueError(f"View '{view.__name__}' already added.")

        # check if name already exists
        for existing_view in self.views:
            if existing_view.name == view.name:
                raise ValueError(f"View with name '{view.name}' already exists")

        # check if path already exists
        for existing_view in self.views:
            if existing_view.path == view.path:
                raise ValueError(f"View with path '{view.path}' already exists")

        # add view
        self._views.append(view)
