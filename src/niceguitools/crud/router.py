import logging
from pathlib import Path
from typing import Callable

from nicegui import APIRouter

from niceguitools.crud.model import CrudModel
from niceguitools.crud.views.base import BaseView
from niceguitools.crud.views.create import CreateView
from niceguitools.crud.views.get import GetView
from niceguitools.crud.views.list import ListView
from niceguitools.crud.views.update import UpdateView

logger = logging.getLogger(__name__)


class CrudRouter(APIRouter):
    def __init__(self,
                 *,
                 model: type[CrudModel],
                 list_view_cls: type[BaseView] | None = ListView,
                 list_view_path: str = "/",
                 list_view_title: str | None = None,
                 list_view_viewport: str | None = None,
                 list_view_favicon: str | Path | None = None,
                 list_view_dark: bool | None = ...,  # type: ignore
                 list_view_response_timeout: float = 3.0,
                 list_view_view_kwargs: dict | None = None,
                 list_view_page_kwargs: dict | None = None,
                 get_view_cls: type[BaseView] | None = GetView,
                 get_view_path: str = "/{id}",
                 get_view_title: str | None = None,
                 get_view_viewport: str | None = None,
                 get_view_favicon: str | Path | None = None,
                 get_view_dark: bool | None = ...,  # type: ignore
                 get_view_response_timeout: float = 3.0,
                 get_view_view_kwargs: dict | None = None,
                 get_view_page_kwargs: dict | None = None,
                 create_view_cls: type[BaseView] | None = CreateView,
                 create_view_path: str = "/create",
                 create_view_title: str | None = None,
                 create_view_viewport: str | None = None,
                 create_view_favicon: str | Path | None = None,
                 create_view_dark: bool | None = ...,  # type: ignore
                 create_view_response_timeout: float = 3.0,
                 create_view_view_kwargs: dict | None = None,
                 create_view_page_kwargs: dict | None = None,
                 update_view_cls: type[BaseView] | None = UpdateView,
                 update_view_path: str = "/{id}/update",
                 update_view_title: str | None = None,
                 update_view_viewport: str | None = None,
                 update_view_favicon: str | Path | None = None,
                 update_view_dark: bool | None = ...,  # type: ignore
                 update_view_response_timeout: float = 3.0,
                 update_view_view_kwargs: dict | None = None,
                 update_view_page_kwargs: dict | None = None,
                 delete_view_cls: type[BaseView] | None = None,
                 delete_view_path: str = "/{id}/delete",
                 delete_view_title: str | None = None,
                 delete_view_viewport: str | None = None,
                 delete_view_favicon: str | Path | None = None,
                 delete_view_dark: bool | None = ...,  # type: ignore
                 delete_view_response_timeout: float = 3.0,
                 delete_view_view_kwargs: dict | None = None,
                 delete_view_page_kwargs: dict | None = None,
                 **kwargs):
        logger.debug(f"Initializing CrudRouter with model '{model.__name__}'")

        super().__init__(**kwargs)

        self.model: type[CrudModel] = model

        # Add default views
        if list_view_cls is not None:
            self.add_view(view_cls=list_view_cls,
                          path=list_view_path,
                          title=list_view_title,
                          viewport=list_view_viewport,
                          favicon=list_view_favicon,
                          dark=list_view_dark,
                          response_timeout=list_view_response_timeout,
                          view_kwargs=list_view_view_kwargs,
                          **(list_view_page_kwargs or {}))
        if get_view_cls is not None:
            self.add_view(view_cls=get_view_cls,
                          path=get_view_path,
                          title=get_view_title,
                          viewport=get_view_viewport,
                          favicon=get_view_favicon,
                          dark=get_view_dark,
                          response_timeout=get_view_response_timeout,
                          view_kwargs=get_view_view_kwargs,
                          **(get_view_page_kwargs or {}))
        if create_view_cls is not None:
            self.add_view(view_cls=create_view_cls,
                          path=create_view_path,
                          title=create_view_title,
                          viewport=create_view_viewport,
                          favicon=create_view_favicon,
                          dark=create_view_dark,
                          response_timeout=create_view_response_timeout,
                          view_kwargs=create_view_view_kwargs,
                          **(create_view_page_kwargs or {}))
        if update_view_cls is not None:
            self.add_view(view_cls=update_view_cls,
                          path=update_view_path,
                          title=update_view_title,
                          viewport=update_view_viewport,
                          favicon=update_view_favicon,
                          dark=update_view_dark,
                          response_timeout=update_view_response_timeout,
                          view_kwargs=update_view_view_kwargs,
                          **(update_view_page_kwargs or {}))
        if delete_view_cls is not None:
            self.add_view(view_cls=delete_view_cls,
                          path=delete_view_path,
                          title=delete_view_title,
                          viewport=delete_view_viewport,
                          favicon=delete_view_favicon,
                          dark=delete_view_dark,
                          response_timeout=delete_view_response_timeout,
                          view_kwargs=delete_view_view_kwargs,
                          **(delete_view_page_kwargs or {}))

        logger.debug(f"CrudRouter initialized with model '{self.model.__name__}'")

    def view(self,
             path: str,
             *,
             title: str | None = None,
             viewport: str | None = None,
             favicon: str | Path | None = None,
             dark: bool | None = ...,  # type: ignore
             response_timeout: float = 3.0,
             view_kwargs: dict | None = None,
             **page_kwargs) -> Callable[[type[BaseView]], type[BaseView]]:
        """
        Decorator to add a view to the router.

        :param path: The path for the view. This will be used to generate the URL for the view.
        :param title: The title for the view. This will be used to set the title of the page when the view is active.
        :param viewport: The viewport for the view. This will be used to set the viewport meta tag for the page when the view is active.
        :param favicon: The favicon for the view. This will be used to set the favicon for the page when the view is active.
        :param dark: Whether to use dark mode for the view. This will be used to set the dark mode for the page when the view is active.
        :param response_timeout: The response timeout for the view. This will be used to set the response timeout for the page when the view is active.
        :param view_kwargs: Additional keyword arguments to pass to the view when it is instantiated. This can be used to pass any additional dependencies that the view may require.
        :param page_kwargs: Additional keyword arguments to pass to the page decorator. This can be used to pass any additional arguments that the page decorator may require.
        :return: A decorator that adds the view to the router.
        """

        def decorator(view_cls: type[BaseView]) -> type[BaseView]:
            self.add_view(view_cls=view_cls,
                          path=path,
                          title=title,
                          viewport=viewport,
                          favicon=favicon,
                          dark=dark,
                          response_timeout=response_timeout,
                          additional_view_kwargs=view_kwargs,
                          **page_kwargs)
            return view_cls

        return decorator

    def add_view(self,
                 path: str,
                 *,
                 title: str | None = None,
                 viewport: str | None = None,
                 favicon: str | Path | None = None,
                 dark: bool | None = ...,  # type: ignore
                 response_timeout: float = 3.0,
                 view_cls: type[BaseView],
                 view_kwargs: dict | None = None,
                 **page_kwargs) -> None:
        """
        Adds a view to the router.

        :param path: The path for the view. This will be used to generate the URL for the view.
        :param title: The title for the view. This will be used to set the title of the page when the view is active.
        :param viewport: The viewport for the view. This will be used to set the viewport meta tag for the page when the view is active.
        :param favicon: The favicon for the view. This will be used to set the favicon for the page when the view is active.
        :param dark: Whether to use dark mode for the view. This will be used to set the dark mode for the page when the view is active.
        :param response_timeout: The response timeout for the view. This will be used to set the response timeout for the page when the view is active.
        :param view_kwargs: Additional keyword arguments to pass to the view when it is instantiated. This can be used to pass any additional dependencies that the view may require.
        :param view_cls: The view class to add. This must be a subclass of BaseView
        :param page_kwargs: Additional keyword arguments to pass to the page decorator. This can be used to pass any additional arguments that the page decorator may require.
        :return: None
        """

        logger.debug(f"Adding view '{view_cls.__name__}' to router with path '{path}'")

        # check if the view class is a subclass of BaseView
        if not issubclass(view_cls, BaseView):
            raise ValueError(f"View class must be a subclass of BaseView, got '{view_cls.__name__}'")

        if view_kwargs is None:
            view_kwargs = {}
        view_kwargs["router"] = self

        async def builder(**kwargs) -> None:
            result = await self.pre_builder_hook(**kwargs)
            if result is not None:
                kwargs = result
            result = await view_cls(**view_kwargs)(**kwargs)
            if result is not None:
                kwargs = result
            await self.post_builder_hook(**kwargs)

        # Set the signature of the builder function to the signature of the view's builder method, so that the correct arguments are passed to the view when it is called.
        builder.__signature__ = view_cls.get_builder_signature()

        self.page(path=path,
                  title=title,
                  viewport=viewport,
                  favicon=favicon,
                  dark=dark,
                  response_timeout=response_timeout,
                  **page_kwargs)(builder)

    async def pre_builder_hook(self, **kwargs) -> dict | None:
        """
        This Hook is called before the builder method of the view is called.
        By default, it does nothing.

        :param kwargs: The keyword arguments that will be passed to the builder method of the view.
        :return: The keyword arguments that will be passed to the builder method of the view. If None is returned, the original keyword arguments will be passed to the builder method of the view.
        """

        pass

    async def post_builder_hook(self, **kwargs) -> None:
        """
        This Hook is called after the builder method of the view is called.
        By default, it does nothing.

        :param kwargs: The keyword arguments that were returned by the builder method of the view.
        :return: None
        """

        pass
