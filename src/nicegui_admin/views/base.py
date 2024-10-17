import logging
from abc import ABC, abstractmethod
from typing import Optional, TYPE_CHECKING, Any

from fastapi.dependencies.utils import ModelField, request_params_to_args
from nicegui.events import EventArguments

if TYPE_CHECKING:
    from nicegui_admin.admin import Admin

logger = logging.getLogger(__name__)


class BaseView(ABC):
    # user defined variables
    name: Optional[str] = None
    path: Optional[str] = None

    def __init__(self,
                 admin: "Admin",
                 render_model_fields: list[ModelField],
                 render_require_event_var: Optional[str]):
        self._admin: "Admin" = admin
        self._render_model_fields: list[ModelField] = render_model_fields
        self._render_require_event_var: Optional[str] = render_require_event_var

    @property
    def admin(self) -> "Admin":
        if self._admin is None:
            raise ValueError("Admin is not set")
        return self._admin

    @property
    def url(self):
        return self.admin.base_path + self.path

    async def __call__(self, event: Optional[EventArguments] = None, query_params: dict[str, Any] = None):
        # set query_params to an empty dict if it's None
        if query_params is None:
            query_params = {}

        # check if all query parameters are accepted
        for key, value in query_params.items():
            if type(value) is not list:
                value = [value]
            found = False
            for field in self._render_model_fields:
                if field.name == key:
                    found = True
                    break
            if not found:
                raise AttributeError(f"Function '{self.render.__name__}' does not accept parameter '{key}'.")  # ToDo: improve error message
            # unpack list query parameters
            if type(value) is list:
                query_params[key] = value.pop()

        # validate and convert query parameters if possible
        query_params, query_errors = request_params_to_args(
            fields=self._render_model_fields,
            received_params=query_params,
        )
        if len(query_errors) > 0:
            raise AttributeError(f"Errors while validating query parameters: {query_errors}")  # ToDo: improve error message

        # generate render kwargs
        render_kwargs = {}

        # add event if required
        if self._render_require_event_var is not None:
            render_kwargs[self._render_require_event_var] = event

        # add query parameters
        for key, value in query_params.items():
            if key in render_kwargs:
                raise AttributeError(f"Parameter '{key}' is already set.")
            render_kwargs[key] = value

        # render the view
        await self.render(**render_kwargs)

    @abstractmethod
    async def render(self, **kwargs: dict[str, Any]):
        ...
