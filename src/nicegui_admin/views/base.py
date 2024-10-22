import inspect
import re
import string
from abc import ABC, ABCMeta, abstractmethod
from enum import Enum
from typing import TYPE_CHECKING, Any

from fastapi.dependencies.utils import ModelField, request_params_to_args, analyze_param
from fastapi.params import Param, Path as PathParam, Query as QueryParam

if TYPE_CHECKING:
    from nicegui_admin.admin import Admin
    from nicegui_admin.layouts.base import BaseLayout


class ParameterMode(Enum):
    STRICT = "strict"
    ALLOW_EXTRA = "allow_extra"


class BaseViewMeta(ABCMeta):
    def __new__(mcs, name, bases, namespace, **kwargs):
        # create cls
        cls = super().__new__(mcs, name, bases, namespace, **kwargs)

        # if name is not set, use the class name
        view_name = namespace.get("name")
        if view_name is None:
            view_name = name

        # normalize name
        normalized_name = mcs.get_normalized_view_name(view_name=view_name)

        # set normalized name
        cls.name = normalized_name

        # if path is not set, use the normalized name
        view_path = namespace.get("path")
        if view_path is None:
            view_path = view_name

        # normalize path and get path parameters
        normalized_path, path_parameters = mcs.get_normalized_view_path_and_path_parameters(view_path=view_path)

        # set normalized path
        cls.path = normalized_path

        # is parameter mode is not set, use the default
        view_parameter_mode = namespace.get("parameter_mode")
        if view_parameter_mode is None:
            view_parameter_mode = ParameterMode.STRICT

        # check if parameter mode is valid
        if not isinstance(view_parameter_mode, ParameterMode):
            try:
                view_parameter_mode = ParameterMode(view_parameter_mode)
            except ValueError as e:
                raise ValueError(f"Invalid parameter mode '{view_parameter_mode}' for '{name}'") from e

        # set parameter mode
        cls.parameter_mode = view_parameter_mode

        # get pydantic model fields for render method
        render_model_fields = mcs.get_pydanctic_model_fields_for_render_method(cls_name=name,
                                                                               render_method=getattr(cls, "render"),
                                                                               path_parameters=path_parameters)

        # set render_model_fields
        cls._render_model_fields = render_model_fields

        return cls

    @classmethod
    def get_normalized_view_name(mcs, view_name: str) -> str:
        # normalize name
        normalized_name = ""
        for c in view_name:
            # if c is uppercase or digit, add a space before it
            if c in string.ascii_uppercase + string.digits:
                normalized_name += " " + c
            # if c is not a letter or digit, replace it with a space
            elif c not in string.ascii_letters + string.digits:
                normalized_name += " "
            else:
                normalized_name += c

        # remove leading and trailing spaces
        normalized_name = re.sub(r"\s+", " ", normalized_name).strip()

        return normalized_name

    @classmethod
    def get_normalized_view_path_and_path_parameters(mcs, view_path: str) -> tuple[str, dict[str, bool]]:
        # normalize path
        view_path = view_path.lower()
        view_path = view_path.replace(" ", "-")
        for c in view_path:
            if c not in string.ascii_lowercase + string.digits + "_-/{}:":  # allowed characters
                raise ValueError(f"Invalid character '{c}' in path '{view_path}'")
        if view_path.startswith("/"):  # remove leading slash
            view_path = view_path[1:]

        # get path parameter names and parse view path
        path_parameters: dict[str, bool] = {}  # (name, capture all following)
        normalized_path = ""
        view_path_segments = view_path.split("/")
        static_path_segment_allowed_chars = string.ascii_lowercase + string.digits + "_-"
        param_path_segment_allowed_chars = string.ascii_lowercase + string.digits + ":_"
        for i, sub_path in enumerate(view_path_segments):
            if len(sub_path) == 0:
                raise ValueError(f"Empty path segment in path '{view_path}'")
            if sub_path.startswith("{"):  # path parameter
                if not sub_path.endswith("}"):
                    raise ValueError(f"Opening bracket '{{' without closing bracket '}}' in path '{view_path}'")
                path_parameter_name = sub_path[1:-1]
                for c in path_parameter_name:
                    if c not in param_path_segment_allowed_chars:
                        raise ValueError(f"Invalid character '{c}' in path parameter '{sub_path}' in path '{view_path}'")
                capture_all_following = False
                if ":" in path_parameter_name:
                    if not path_parameter_name.endswith(":_"):
                        raise ValueError(f"Invalid path parameter '{sub_path}' in path '{view_path}'. Capture all following parameter must end with ':_'")
                    if i != len(view_path_segments) - 1:
                        raise ValueError(f"Capture all following parameter can only be used at the end of the path '{view_path}'")
                    capture_all_following = True
                    path_parameter_name = path_parameter_name[:-2]
                if path_parameter_name in path_parameters:
                    raise ValueError(f"Path parameter '{path_parameter_name}' already exists in path '{view_path}'")
                path_parameters[path_parameter_name] = capture_all_following
            else:  # static path segment
                if len(path_parameters) > 0:
                    raise ValueError(f"Static path segments after path parameter are not allowed in path '{view_path}'")
                for c in sub_path:
                    if c not in static_path_segment_allowed_chars:
                        raise ValueError(f"Invalid character '{c}' in static path segment '{sub_path}' in path '{view_path}'")
                normalized_path += sub_path + "/"

        # remove trailing slash
        if normalized_path.endswith("/"):
            normalized_path = normalized_path[:-1]

        # add leading slash
        normalized_path = "/" + normalized_path

        return normalized_path, path_parameters

    @classmethod
    def get_pydanctic_model_fields_for_render_method(mcs, cls_name: str, render_method: callable, path_parameters: dict[str, bool]) -> list[ModelField]:
        # get pydantic model fields for render method
        render_signature = inspect.signature(render_method)
        render_model_fields: list[ModelField] = []
        capture_all_following_set = None
        var_keyword_name = None
        for param in render_signature.parameters.values():
            # skip self parameter
            if param.name == "self":
                continue

            # check if the parameter is a path parameter
            is_path_param = param.name in path_parameters or param.kind == inspect.Parameter.VAR_POSITIONAL

            # get the field for the parameter
            param_details = analyze_param(
                param_name=param.name,
                annotation=param.annotation,
                value=param.default,
                is_path_param=is_path_param,
            )
            field = param_details.field

            # set 'capture_all_following' to json_schema_extra and remove it from path_parameters
            if is_path_param:
                if param.default is not param.empty:
                    raise AttributeError(f"Path parameter '{param.name}' for '{cls_name}.{render_method.__name__}' cannot have a default value")


                if capture_all_following_set is not None:
                    raise AttributeError(f"Path parameter '{param.name}' for '{cls_name}.{render_method.__name__}' is not allowed after '{capture_all_following_set}'")
                capture_all_following = path_parameters.get(param.name, True)
                if capture_all_following:
                    capture_all_following_set = field.name
                field.field_info.json_schema_extra["capture_all_following"] = capture_all_following
                if param.name in path_parameters:
                    path_parameters.pop(param.name)

            # set 'var_positional' to json_schema_extra
            field.field_info.json_schema_extra["var_positional"] = param.kind == inspect.Parameter.VAR_POSITIONAL

            # set 'var_keyword' to json_schema_extra
            field.field_info.json_schema_extra["var_keyword"] = param.kind == inspect.Parameter.VAR_KEYWORD

            # set 'var_keyword_available' to True if the parameter is a var_keyword
            if param.kind == inspect.Parameter.VAR_KEYWORD:
                var_keyword_name = param.name
                field.field_info.json_schema_extra["var_keyword_takes"] = {}

                # check if the field is a Param
            if not isinstance(field.field_info, Param):
                raise AttributeError(f"Parameter '{param.name}' for '{cls_name}.{render_method.__name__}' with type '{param.annotation}' is not supported.")

            # add the field to the list of fields
            render_model_fields.append(field)

        # check if there are any path parameters left
        if len(path_parameters) > 0:
            if var_keyword_name is None:
                raise AttributeError(f"Path parameters '{list(path_parameters.keys())}' are not used in '{cls_name}.{render_method.__name__}'")
            for render_model_field in render_model_fields:
                if render_model_field.name == var_keyword_name:
                    render_model_field.field_info.json_schema_extra["var_keyword_takes"] = path_parameters
                    path_parameters = {}
            if len(path_parameters) > 0:
                raise AttributeError(f"Path parameters '{list(path_parameters.keys())}' are not used in '{cls_name}.{render_method.__name__}'")

        return render_model_fields


class BaseView(ABC, metaclass=BaseViewMeta):
    # user defined variables
    name: str
    path: str
    parameter_mode: ParameterMode

    # internal variables
    _render_model_fields: list[ModelField]

    def __init__(self,
                 layout: "BaseLayout"):
        self._layout: "BaseLayout" = layout
        # self._render_model_fields: list[ModelField] = render_model_fields

    def __str__(self):
        name = self.name
        path = self.path
        return f"{self.__class__.__name__}({name=}, {path=})"

    @property
    def layout(self) -> "BaseLayout":
        if self._layout is None:
            raise ValueError("Layout is not set")
        return self._layout

    @property
    def admin(self) -> "Admin":
        return self.layout.admin

    @property
    def url(self):
        return self.admin.base_path + self.path

    async def validate(self,
                       path_parameters_values: list[str] = None,
                       query_params: dict[str, list[str]] = None) -> tuple[tuple[Any, ...], dict[str, Any], list[dict]]:
        # set path_parameters_values to an empty list if it's None
        if path_parameters_values is None:
            path_parameters_values = []

        # set query_params to an empty dict if it's None
        if query_params is None:
            query_params = {}

        render_model_fields = self._render_model_fields.copy()

        # get QueryParam fields
        received_params = {}
        capture_all_following_done = False
        var_keyword_name = None
        for render_model_field in render_model_fields.copy():
            if type(render_model_field.field_info) is not QueryParam:
                continue
            if render_model_field.field_info.json_schema_extra["var_keyword"]:
                if var_keyword_name is not None:
                    raise RuntimeError("Variable keyword name is already set")
                var_keyword_name = render_model_field.name
                received_params[render_model_field.name] = {}
                if capture_all_following_done:
                    raise RuntimeError("Mapping for path parameters is finished, but there are still path parameters left.")
                for path_param_name, capture_all_following in render_model_field.field_info.json_schema_extra["var_keyword_takes"].items():
                    if len(path_parameters_values) == 0:
                        continue
                    if not capture_all_following:
                        # noinspection PyTypeChecker
                        received_params[render_model_field.name][path_param_name] = path_parameters_values.pop(0)
                    else:
                        received_params[render_model_field.name][path_param_name] = "/".join(path_parameters_values)
                        path_parameters_values = []
                        capture_all_following_done = True
                for key, value in query_params.items():
                    if key in received_params[render_model_field.name]:
                        raise RuntimeError(f"Query parameter '{key}' is already set as a path parameter")
                    # noinspection PyTypeChecker
                    received_params[render_model_field.name][key] = value.pop(0)
                query_params = {}
            else:
                value = query_params.pop(render_model_field.name, None)
                if value is not None:
                    # noinspection PyTypeChecker
                    received_params[render_model_field.name] = value.pop(0)
            render_model_fields.remove(render_model_field)

        # get PathParam fields
        path_position = 0
        var_positional_name = None
        for render_model_field in render_model_fields.copy():
            if type(render_model_field.field_info) is not PathParam:
                continue
            path_position += 1
            if render_model_field.field_info.json_schema_extra["var_positional"]:
                if var_positional_name is not None:
                    raise RuntimeError("Variable positional name is already set")
                var_positional_name = render_model_field.name
                received_params[render_model_field.name] = []
            if len(path_parameters_values) == 0:
                render_model_fields.remove(render_model_field)
                continue
            if capture_all_following_done:
                raise RuntimeError("Mapping for path parameters is finished, but there are still path parameters left.")
            capture_all_following = render_model_field.field_info.json_schema_extra["capture_all_following"]
            if capture_all_following:
                capture_all_following_done = True
            if not capture_all_following:
                # noinspection PyTypeChecker
                value = path_parameters_values.pop(0)
                if render_model_field.name == var_positional_name:
                    received_params[render_model_field.name].append(value)
                else:
                    received_params[render_model_field.name] = value
            else:
                if render_model_field.name == var_positional_name:
                    received_params[render_model_field.name].extend(path_parameters_values)
                else:
                    received_params[render_model_field.name] = "/".join(path_parameters_values)
                path_parameters_values = []
            render_model_fields.remove(render_model_field)

        # check if there are any render_model_fields left
        if len(render_model_fields) > 0:
            map_errors = []
            for render_model_field in render_model_fields:
                map_errors.append(f"Field '{render_model_field.name}' is not a {PathParam.__name__} or {QueryParam.__name__}")
            raise RuntimeError(map_errors)

        # validate and convert query parameters if possible
        validated_kwargs, param_errors = request_params_to_args(
            fields=self._render_model_fields,
            received_params=received_params,
        )

        # if parameter_mode is set to strict, check if there are any path or query parameters left
        if self.parameter_mode == ParameterMode.STRICT:
            for path_param in path_parameters_values:
                param_errors.append({"input": path_param,
                                     "loc": ("path", path_position),
                                     "msg": "Additional path parameter is not allowed in strict mode",
                                     "type": "value_error"})
            for query_param in query_params:
                param_errors.append({"input": query_param,
                                     "loc": ("query", query_param),
                                     "msg": "Additional query parameter is not allowed in strict mode",
                                     "type": "value_error"})

        # separate validated_kwargs into args and kwargs
        args = []
        kwargs = {}
        if var_positional_name is not None:
            args = validated_kwargs.pop(var_positional_name)
        if var_keyword_name is not None:
            kwargs = validated_kwargs.pop(var_keyword_name)
        kwargs.update(validated_kwargs)

        return args, kwargs, param_errors

    @abstractmethod
    async def render(self, *args, **kwargs):
        ...
