import inspect
from inspect import Signature
from pathlib import Path
from typing import TYPE_CHECKING, Any

from nicegui import ui

from niceguitools._crud.fields.base import BaseField
from niceguitools._crud.model import CrudModel

if TYPE_CHECKING:
    from niceguitools._crud.router import CrudRouter


class BaseView:
    def __init__(self, router: "CrudRouter", debug: bool = False):
        self.router: "CrudRouter" = router
        self.debug: bool = debug

    @property
    def model(self) -> type[CrudModel]:
        return self.router.model

    @property
    def fields(self) -> dict[str, BaseField]:
        fields = {}
        for field_name, field in self.model.get_crud_fields().items():
            # skip fields that are hidden in this view
            if field.hide is True:
                continue
            if isinstance(field.hide, list):
                hide = False
                for hide_view in field.hide:
                    if issubclass(type(self), hide_view):
                        hide = True
                        break
                if hide:
                    continue

            fields[field_name] = field
        return fields


    @classmethod
    def get_builder_signature(cls) -> Signature:
        builder_signature = inspect.signature(cls.builder)

        # filter VAR_POSITIONAL and VAR_KEYWORD parameters
        filtered_parameter = {key: value for key, value in inspect.signature(cls.builder).parameters.items() if
                              value.kind not in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD)}

        # remove the 'self' parameter
        filtered_parameter.pop("self", None)

        # replace the signature parameters with the filtered ones
        builder_signature = builder_signature.replace(parameters=list(filtered_parameter.values()))

        return builder_signature

    async def __call__(self, **kwargs) -> dict:
        if self.debug:
            await self._debug(**kwargs)
        result = await self.pre_builder_hook(**kwargs)
        if result is not None:
            kwargs = result
        result = await self.builder(**kwargs)
        if result is not None:
            kwargs = result
        result = await self.post_builder_hook(**kwargs)
        if result is not None:
             kwargs = result
        return kwargs

    async def _debug(self, **kwargs) -> None:
        ui.label(self.__class__.__name__)
        if len(kwargs) > 0:
            ui.label("Arguments passed to builder:")
            for key, value in kwargs.items():
                ui.label(f"{key}: {value}")
        else:
            ui.label("No arguments passed to builder.")

    async def pre_builder_hook(self, **kwargs) -> dict | None:
        """
        Hook method that is called before the builder method. Can be used to modify the arguments passed to the builder method.
        By default, it does nothing.

        :param kwargs: The keyword arguments that will be passed to the builder method of the view.
        :return: The modified keyword arguments that will be passed to the builder method of the view. If None is returned, the original keyword arguments will be passed to the builder method.
        """

        pass

    async def builder(self, **kwargs) -> dict | None:
        """
        The builder method that must be implemented by the child class.
        This method is responsible for building the view and returning the arguments that will be passed to the router.

        :param kwargs: The keyword arguments that were returned by the pre_builder_hook method.
        :return: The keyword arguments that will be passed to post_builder_hook. If None is returned, the original keyword arguments passed to the builder method will be passed to post_builder_hook.
        """

        raise NotImplementedError("The builder method must be implemented by the child class.")

    async def post_builder_hook(self, **kwargs) -> dict | None:
        """
        Hook method that is called after the builder method. Can be used to modify the arguments returned by the builder method.
        By default, it does nothing.

        :param kwargs: The keyword arguments that were returned by the builder method of the view.
        :return: The modified keyword arguments that will be passed to the router. If None is returned, the original keyword arguments returned by the builder method will be passed to the router.
        """

        return kwargs
