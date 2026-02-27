from typing import Callable

from nicegui import APIRouter

from nicegui_admin.helpers import Unset
from nicegui_admin.sub_page import SubPageApp
from nicegui_admin.views import BaseView


class BaseAdmin(SubPageApp):
    """
    Base class for implementing Admin interface.
    """

    def __init__(self,
                 title: str = Unset,
                 **kwargs):
        """
        :param title: Admin title.
        :param kwargs: Other keyword arguments to be passed to the APIRouter constructor.
        """

        SubPageApp.__init__(self, **kwargs)

        self.title: str = Unset.resolve(title, "Admin")
        self._views: list[BaseView] = []

        self.page("/{_:path}")(self.builder)

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

        view_instance: BaseView = view if isinstance(view, BaseView) else view(**kwargs)
        if view_instance in self.views:
            raise ValueError(f"View with path '{view_instance.path}' already exists.")
        if getattr(view, "_admin", None) is not None:
            raise ValueError(f"View '{view_instance}' is already assigned to an admin.")
        setattr(view, "_admin", self)
        self._views.append(view_instance)
        self.include_subpage_router(view_instance,
                                    prefix=view_instance.path)
