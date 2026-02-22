from pathlib import Path
from typing import Callable

from nicegui import APIRouter

from niceguitools.admin.helper import Unset
from niceguitools.admin.page import Page
from niceguitools.admin.views import BaseView


class BaseAdmin(APIRouter):
    """
    Base class for implementing Admin interface.
    """

    def __init__(self,
                 title: str = Unset,
                 page_cls: type[Page] = Unset,
                 **kwargs):
        """
        :param title: Admin title.
        :param kwargs: Other keyword arguments to be passed to the APIRouter constructor.
        """

        super().__init__(**kwargs)

        self.title: str = Unset.resolve(title, "Admin")
        self.page_cls: type[Page] = Unset.resolve(page_cls, Page)
        self._views: list[BaseView] = []

    @property
    def views(self) -> tuple[BaseView, ...]:
        """
        All views added to the Admin interface.

        :return: Tuple of all views added to the Admin interface.
        """

        return tuple(self._views)

    def view(self, **kwargs) -> Callable[[type[BaseView]], type[BaseView]]:
        """
        Decorator for adding views to the Admin interface.

        :param kwargs: Keyword arguments to be passed to the view constructor.
        :return: Decorator function that takes a view class and adds it to the Admin interface.
        """

        def decorator(view: type[BaseView]) -> type[BaseView]:
            self.add_view(view=view, **kwargs)
            return view

        return decorator

    def add_view(self,
                 view: type[BaseView] | BaseView,
                 **kwargs) -> None:
        """
        Add View to the Admin interface.

        :param view: View to be added. Can be either a class or an instance of BaseView.
        :param kwargs: Keyword arguments to be passed to the view constructor if view is a class.
        :return: None
        """

        view_instance = view if isinstance(view, BaseView) else view(**kwargs)
        if view_instance in self.views:
            raise ValueError(f"View with path '{view_instance.path}' already exists.")
        if getattr(view, "_admin", None) is not None:
            raise ValueError(f"View '{view_instance}' is already assigned to an admin.")
        setattr(view, "_admin", self)
        self._views.append(view_instance)

    # def page(self,
    #          path: str, *,
    #          title: str | None = None,
    #          viewport: str | None = None,
    #          favicon: str | Path | None = None,
    #          dark: bool | None = ...,  # type: ignore
    #          response_timeout: float = 3.0,
    #          **kwargs) -> Callable:
    #     """
    #     Decorator for creating a new page for view.
    #     Creates a new page at the given route.
    #     Each user will see a new instance of the page.
    #     This means it is private to the user and not shared with others.
    #
    #     :param path: route of the new page (path must start with '/')
    #     :param title: optional page title
    #     :param viewport: optional viewport meta tag content
    #     :param favicon: optional relative filepath or absolute URL to a favicon (default: `None`, NiceGUI icon will be used)
    #     :param dark: whether to use Quasar's dark mode (defaults to `dark` argument of `run` command)
    #     :param response_timeout: maximum time for the decorated function to build the page (default: 3.0)
    #     :param kwargs: additional keyword arguments passed to FastAPI's @app.get method
    #     """
    #
    #     return self.page_cls(path=path,
    #                          title=title,
    #                          viewport=viewport,
    #                          favicon=favicon,
    #                          dark=dark,
    #                          response_timeout=response_timeout,
    #                          api_router=self,
    #                          **kwargs)

