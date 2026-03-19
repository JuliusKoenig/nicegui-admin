import logging
import traceback
from dataclasses import dataclass, field, fields
from pathlib import Path
from typing import Any, Callable, TYPE_CHECKING, Union

from fastapi import HTTPException
from nicegui import ui

from nicegui_admin.elements.sub_page import SubPages
from nicegui_admin.helpers import DecoratedMethodClass, decorate, Unset, prettify_name
from nicegui_admin.types import SyncOrAsyncMethod

if TYPE_CHECKING:
    from nicegui_admin.views import BaseView

logger = logging.getLogger(__name__)
CSS_FILE_PATH = Path(__file__).parent / "style.css"

with CSS_FILE_PATH.open("r") as f:
    content = f.read()
    ui.add_css(content=content,
               shared=True)


def sub_page(path: str,
             *,
             title: str | None = Unset,
             icon: str | Path | None = None):
    """
    Decorator for adding a SubPage to the SubPage router.
    Before instantiating the SubPage router, this decorator will not do anything.
    It is possible to simple override the SubPage builder function in subclasses of the SubPage router without using this decorator again.
    After the SubPage router is instantiated, this decorator will do nothing.

    :param path: Path of the SubPage. Should be unique among all SubPages added to the SubPage router.
    :param title: Title of the SubPage. If not provided, the title will be inferred from the builder function name.
    :param icon: Icon of the SubPage. Can be either a URL or a local file path. If not provided, no icon will be set for the SubPage.
    :return: Decorator function that takes a builder function and adds it as a SubPage to the SubPage router.
    """

    return decorate("sub_page",
                    path=path,
                    title=title,
                    icon=icon)




@dataclass
class BaseAdmin(DecoratedMethodClass):
    """
    Base class for implementing Admin interface.

    :param debug: Enable debug mode. If True, error pages will display detailed error information and stack traces.
    :param path: The path for this Admin interface. Should be unique among all Admin interfaces in the application. Should start with '/' and should not end with '/'. Defaults to "/admin".
    :param title: Admin interface title. Defaults to "Admin".
    """

    debug: bool | Unset = field(default=Unset)
    path: str | Unset = field(default=Unset, metadata={"immutable": True})
    title: str | Unset = field(default=Unset)
    _views: list["BaseView"] = field(default_factory=list, init=False)
    _initialized: bool = field(default=False, init=False)

    def __post_init__(self):
        self.debug: bool = Unset.resolve(self.debug, False)
        self.path: str = Unset.resolve(self.path, "/admin")
        if not self.path.startswith("/"):
            self.path = "/" + self.path
        if self.path.endswith("/"):
            self.path = self.path[:-1]
        self.title: str = Unset.resolve(self.title, "Admin")

        ui.page(f"{self.path}/{{_:path}}")(self.root)
        self._initialized = True

    def __setattr__(self, key, value):
        if key == "_initialized":
            return super().__setattr__(key, value)
        immutable_field_names = []
        for _field in fields(self.__class__):
            if _field.metadata.get("immutable", False):
                immutable_field_names.append(_field.name)
        if key in immutable_field_names and self._initialized:
            raise RuntimeError("Cannot set attributes after the Admin has been initialized.")
        return super().__setattr__(key, value)

    @property
    def sub_pages(self) -> dict[str, dict[str, Any]]:
        """
        All SubPages added to this SubPageRouter using the @sub_page decorator or the add_sub_page method.
        :return: A dictionary where the keys are the paths of the SubPages and the values
         are dictionaries containing the builder function and attributes of the SubPages, such as title and icon.
        """

        sub_pages = {}
        for builder, kwargs in self.__decorated_methods__.get("sub_page", {}).items():
            path = self.path + kwargs["path"]
            if path.endswith("/"):
                path = path[:-1]
            title = Unset.resolve(kwargs["title"], prettify_name(builder.__name__))
            icon = kwargs["icon"]
            sub_pages[path] = {"builder": builder,
                               "title": title,
                               "icon": icon}

        for view in self.views:
            for path, sub_page_dict in view.sub_pages.items():
                sub_pages[self.path + path] = sub_page_dict

        return sub_pages

    def sub_page(self,
                 path: str,
                 *,
                 title: str | None = Unset,
                 icon: str | Path | None = None) -> SyncOrAsyncMethod:
        """
        Decorator for adding a SubPage to the SubPage router.
        Use this decorator after instantiating the SubPage router to add builder functions for the SubPages.

        :param path: Path of the SubPage. Should be unique among all SubPages added to the SubPage router.
        :param title: Title of the SubPage. If not provided, the title will be inferred from the builder function name.
        :param icon: Icon of the SubPage. Can be either a URL or a local file path. If not provided, no icon will be set for the SubPage.
        :return: Decorator function that takes a builder function and adds it as a SubPage to the SubPage router.
        """

        return self.__decorate__("sub_page",
                                 path=path,
                                 title=title,
                                 icon=icon)

    # rename favicon to icon
    def add_sub_page(self,
                     builder: SyncOrAsyncMethod,
                     path: str,
                     *,
                     title: str | None = Unset,
                     icon: str | Path | None = None) -> None:
        """
        Add a SubPage to the SubPage router.

        :param builder: Builder function for the SubPage. Can be either a regular function or an async function that builds the page content when called.
        :param path: Path of the SubPage. Should be unique among all SubPages added to the SubPage router.
        :param title: Title of the SubPage. If not provided, the title will be inferred from the builder function name.
        :param icon: Icon of the SubPage. Can be either a URL or a local file path. If not provided, no icon will be set for the SubPage.
        :return: None
        """

        self.__add_decoration__(builder,
                                "sub_page",
                                path=path,
                                title=title,
                                icon=icon)

    @property
    def views(self) -> tuple["BaseView", ...]:
        """
        All views added to the Admin interface.

        :return: Tuple of all views added to the Admin interface.
        """

        return tuple(self._views)

    def view(self, **kwargs) -> Callable[[type["BaseView"]], type["BaseView"]]:
        """
        Decorator for adding views to the Admin interface.

        :param kwargs: Keyword arguments to be passed to the view constructor.
        :return: Decorator function that takes a view class and adds it to the Admin interface.
        """

        def decorator(view: type["BaseView"]) -> type["BaseView"]:
            self.add_view(view=view, **kwargs)
            return view

        return decorator

    def add_view(self,
                 view: Union[type["BaseView"], "BaseView"],
                 **kwargs) -> None:
        """
        Add View to the Admin interface.

        :param view: View to be added. Can be either a class or an instance of BaseView.
        :param kwargs: Keyword arguments to be passed to the view constructor if view is a class.
        :return: None
        """

        view_instance: "BaseView" = view
        if isinstance(view, type):
            view_instance = view(**kwargs)
        if view_instance in self.views:
            raise ValueError(f"View with path '{view_instance.path}' already exists.")
        if getattr(view, "_admin", None) is not None:
            raise ValueError(f"View '{view_instance}' is already assigned to an admin.")
        setattr(view, "_admin", self)
        self._views.append(view_instance)

    async def root(self) -> None:
        dark_mode = ui.dark_mode()
        ui.button("Toggle Dark Mode",
                  on_click=lambda: dark_mode.toggle())

        SubPages(self).classes("w-full")

    def error_page(self,
                   status_code: int | Unset = Unset,
                   title: str | Unset = Unset,
                   icon: str | Unset | None = Unset,
                   color: str | Unset | None = Unset,
                   message: str | Unset | None = Unset,
                   error: Exception | None = None,
                   buttons: bool = True,
                   log: bool = True) -> None:
        """
        Renders an error page with the given title, icon, color, and message.
        If the SubPageApp is in debug mode and an error is provided, the stack trace of the error will also be displayed on the error page.

        :param status_code: The HTTP status code to be returned with the error page. Defaults to 500.
        :param title: The title of the error page.
        :param icon: The icon to be displayed on the error page. Can be either a URL or a local file path. If not provided, no icon will be displayed on the error page.
         Note that favicon for error pages is not yet supported, so the icon will be ignored and a warning will be logged if an icon is provided.
        :param color: The color to be used for the title and icon of the error page. Should be a valid Tailwind CSS color. If not provided, the default color "red" will be used.
        :param message: An optional message to be displayed on the error page below the title. If not provided, no message will be displayed on the error page.
        :param error: An optional exception that was raised while rendering the page. The SubPageApp must be in debug mode for the stack trace of the error to be displayed on the error page.
        :param buttons: If True, "Go Home" and "Go Back" buttons will be displayed on the error page to allow for easy navigation. Defaults to True.
        :param log: If True, the error message and stack trace (if available) will be logged using the logger. Defaults to True.
        :return: None
        """

        if isinstance(error, HTTPException):
            status_code = Unset.resolve(status_code, error.status_code)
            if status_code == 404:
                title = Unset.resolve(message, error.detail)
                icon = Unset.resolve(icon, "search_off")
                message = None
            if self.debug:
                title = Unset.resolve(title, error.__class__.__name__)
                message = Unset.resolve(message, error.detail)

        status_code = Unset.resolve(status_code, 500)
        title = Unset.resolve(title, "Internal Server Error")
        icon = Unset.resolve(icon, "error_outline")
        color = Unset.resolve(color, "red")
        message = Unset.resolve(message, "An unexpected error occurred.")

        # ToDo: implement favicon for error pages
        ui.page_title(f"(Debug Mode) - {title}" if self.debug else title)
        log_msg = title
        with ui.scroll_area().classes("absolute-center w-full h-full pl-4 pr-4"), ui.column().classes("items-center w-full"):
            # icon
            if icon is not None:
                _icon = ui.icon(icon, size="4rem")
                if color is not None:
                    _icon.classes(f"text-{color}")

            # caption
            _status_code_title = ui.label(str(status_code)).classes("text-8xl")
            if color is not None:
                _status_code_title.classes(f"text-{color}")
            _title = ui.label(title).classes("text-2xl")
            if color is not None:
                _title.classes(f"text-{color}")

            # message
            if message is not None:
                ui.label(message).classes("text-gray-600")
                log_msg += f" -> {message}"

            # debug info
            if self.debug:
                with ui.card().classes("w-400 items-center").props('flat bordered') as card:
                    ui.label(f"(Debug Mode)").classes("text-xl")
                    ui.label("SubPages:")
                    with ui.row():
                        for path, kwargs in self.sub_pages.items():
                            ui.link(kwargs["title"], target=path)
            if error is not None and self.debug:
                with card:
                    stack_trace = traceback.format_exc()
                    ui.code(stack_trace).classes("w-full text-left bg-grey-100")
                    log_msg += f"\n{stack_trace}"

            # navigation buttons
            if buttons:
                with ui.row().classes("mt-4"):
                    ui.button("Go Home", icon="home", on_click=lambda: ui.navigate.to(self.admin.prefix)).props("outline")
                    ui.button("Go Back", icon="arrow_back", on_click=ui.navigate.back).props("outline")

        # log error
        if log:
            logger.error(log_msg)
