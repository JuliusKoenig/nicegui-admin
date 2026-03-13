import asyncio
import logging
import traceback
from pathlib import Path
from typing import Any, Callable, Optional, TYPE_CHECKING, Union

from fastapi import HTTPException
from nicegui import ui, background_tasks
from nicegui.page_arguments import RouteMatch, PageArguments

from nicegui_admin.helpers import DecoratedMethodClass, decorate, Unset, prettify_name
from nicegui_admin.types import SyncOrAsyncFunction

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


class SubPageRouter(DecoratedMethodClass):
    """
    Class for routing to different SubPages based on the URL path.
    """

    class SubPages(ui.sub_pages):
        """
        Custom implementation of the SubPages component that supports both routing to builder functions and including other SubPageRouters as sub-pages.
        The routes are dynamically generated based on the included SubPageRouters and the builder functions decorated with the @sub_page decorator.
        """

        def __init__(self, sub_page_router: "SubPageRouter") -> None:
            self.sub_page_router: "SubPageRouter" = sub_page_router
            super().__init__(show_404=True)

        @property
        def _routes(self) -> dict[str, SyncOrAsyncFunction]:
            """
            The routes for the SubPages component.

            :return: The keys are the paths of the SubPages and the values are the builder functions that should be called when navigating to the corresponding path.
            """

            routes = {}
            for router in self.sub_page_router.sub_page_router:
                routes[router.prefix] = router.root
            for path, kwargs in self.sub_page_router.sub_pages.items():
                if self._root_path is not None:
                    path = path[len(self._root_path):] if path.startswith(self._root_path) else path
                builder: SyncOrAsyncFunction = kwargs["builder"]
                routes[path] = builder
            return routes

        @property
        def _builder_attributes(self) -> dict[SyncOrAsyncFunction, dict[str, Any]]:
            """
            Builder attributes for the SubPages component.

            :return: The keys are the builder functions and the values are dictionaries containing the attributes of the builders, such as title and icon.
            """

            builder_attributes = {}
            for path, kwargs in self.sub_page_router.sub_pages.items():
                builder_attributes[kwargs["builder"]] = kwargs
            return builder_attributes

        @_routes.setter
        def _routes(self, value: dict[str, Callable]) -> None:
            """
            Does nothing, as the routes are dynamically generated based on the included SubPageRouters
            and the builder functions decorated with the @sub_page decorator.
            """

            ...

        def _render_page(self, match: RouteMatch) -> bool:
            """
            Renders the page corresponding to the given route match.
            If the route match corresponds to a builder function, the builder function is called to render the page content.

            :param match: The route match for the page to be rendered. Contains information about the path and the builder function to be called.
            :return: True if the page was rendered successfully, False otherwise.
            """

            kwargs = PageArguments.build_kwargs(match, self, self._data)
            self._rendered_path = f'{self._root_path or ""}{match.path}'
            try:
                builder_attributes = self._builder_attributes.get(match.builder, {})
                title = builder_attributes.get("title")
                if title is not None:
                    ui.page_title(title)
                icon = builder_attributes.get("icon")
                if icon is not None:
                    # ToDo: support favicon for SubPages
                    logger.warning(f"Favicon for SubPages is not yet supported. Ignoring icon '{icon}' for page '{match.path}'.")
                result = match.builder(**kwargs)
            except Exception as e:
                self._render_error(e)
                self.client.handle_exception(e)
                return True

            self._handle_scrolling(match, behavior="instant")
            if asyncio.iscoroutine(result):
                async def background_task():
                    with self:
                        try:
                            await result
                        except Exception as e:
                            self._render_error(e)
                            self.client.handle_exception(e)

                task = background_tasks.create(background_task(), name=f"building sub_page {match.pattern}")
                self._active_tasks.add(task)

                def _close_if_canceled(t: asyncio.Task) -> None:
                    if t.cancelled():
                        result.close()
                    self._active_tasks.discard(t)

                task.add_done_callback(_close_if_canceled)
            return True

        def _render_404(self) -> None:
            """
            Renders a 404 error page when the requested page is not found.

            :return: None
            """

            raise HTTPException(status_code=404, detail=f"The page '{self._router.current_path}' does not exist.")

        def _render_error(self, error: Exception) -> None:
            """
            Renders a 500 error page when an error occurs while rendering the requested page.

            :param error: The exception that was raised while rendering the page.
            The error message and stack trace will be displayed on the error page if the SubPageApp is in debug mode.
            :return: None
            """

            self.clear()
            self.sub_page_router.error_page(error=error,
                                            buttons=True,
                                            log=True)

        def _set_match(self, match: RouteMatch | None) -> None:
            """
            Overwritten to ensure that the 404 page is only shown when no route matches,
            and not when a route matches but an error occurs while rendering the page.
            """
            try:
                super()._set_match(match=match)
            except HTTPException as e:
                self._render_error(e)
            self.has_404 = False

    def __init__(self,
                 prefix: str | Unset = Unset) -> None:
        """
        :param prefix: The path prefix for this SubPageApp. Should start with '/' and should not end with '/'.
        """

        self._parent_sub_page_router: Optional[SubPageRouter] = None
        self._sub_page_router: list[SubPageRouter] = []

        prefix = Unset.resolve(prefix, "")

        # validate prefix
        if prefix:
            assert prefix.startswith("/"), "A path prefix must start with '/'"
            assert not prefix.endswith("/"), (
                "A path prefix must not end with '/', as the routes will start with '/'"
            )
        self._prefix = prefix

    @property
    def admin(self) -> "BaseAdmin":
        """
        The admin instance that this SubPageRouter is included in.

        :return: The SubPageApp instance that this SubPageRouter is included in.
        If the router is not included in any SubPageApp instance, a RuntimeError is raised.
        """

        admin = self
        if self.parent_sub_page_router is not None:
            admin = self.parent_sub_page_router.admin
        if not isinstance(admin, BaseAdmin):
            raise RuntimeError("The router is not included in a admin instance. "
                               "Please include the router in a admin instance using the 'include_sub_page_router' method.")
        return admin

    @property
    def parent_sub_page_router(self) -> Optional["SubPageRouter"]:
        """
        The parent SubPageRouter instance that this SubPageRouter is included in, or None if this SubPageRouter is not included in any other SubPageRouter.
        :return: SubPageRouter or None
        """

        return self._parent_sub_page_router

    @property
    def sub_page_router(self) -> tuple["SubPageRouter", ...]:
        """
        All SubPageRouter instances included in this SubPageRouter.

        :return: Tuple of all SubPageRouter instances included in this SubPageRouter.
        """

        return tuple(self._sub_page_router)

    @property
    def prefix(self) -> str:
        """
        The path prefix for this SubPageRouter. The prefix is used to determine the URL path for the SubPages included in this router.
        If this SubPageRouter is included in another SubPageRouter, the prefix of the parent router is prepended to the prefix of this router.
        :return: The path prefix for this SubPageRouter.
        """

        if self.parent_sub_page_router is not None:
            return self.parent_sub_page_router.prefix + self._prefix
        return self._prefix

    @prefix.setter
    def prefix(self, value: str) -> None:
        if value:
            assert value.startswith("/"), "A path prefix must start with '/'"
            assert not value.endswith("/"), (
                "A path prefix must not end with '/', as the routes will start with '/'"
            )
        self._prefix = value

    @property
    def sub_pages(self) -> dict[str, dict[str, Any]]:
        """
        All SubPages added to this SubPageRouter using the @sub_page decorator or the add_sub_page method.
        :return: A dictionary where the keys are the paths of the SubPages and the values
         are dictionaries containing the builder function and attributes of the SubPages, such as title and icon.
        """

        sub_pages = {}
        for builder, kwargs in self.__decorated_methods__.get("sub_page", {}).items():
            path = self.prefix + kwargs["path"]
            title = Unset.resolve(kwargs["title"], prettify_name(builder.__name__))
            icon = kwargs["icon"]
            sub_pages[path] = {"builder": builder,
                               "title": title,
                               "icon": icon}

        return sub_pages

    def sub_page(self,
                 path: str,
                 *,
                 title: str | None = Unset,
                 icon: str | Path | None = None) -> SyncOrAsyncFunction:
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
                     builder: SyncOrAsyncFunction,
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

    def include_sub_page_router(self,
                                router: "SubPageRouter",
                                *,
                                prefix: str | Unset = Unset) -> None:
        """
        Include another SubPageRouter as a sub-page of this SubPageRouter. This allows for nesting of SubPageRouters and better organization of the page structure.
        The included SubPageRouter will be accessible at the URL path determined by the prefix parameter.
        If the prefix parameter is not provided, the prefix of the included SubPageRouter will be used as the path prefix for the included SubPageRouter.
        The prefix of the included SubPageRouter is always relative to the prefix of this SubPage.

        :param router: The SubPageRouter instance to be included as a sub-page of this SubPageRouter.
        :param prefix: The path prefix for the included SubPageRouter. Should start with '/' and should not end with '/'.
        :return: None
        """

        if self is router:
            ValueError("Cannot include the same SupPageRouter instance into itself. "
                       "Did you mean to include a different router?")
        if router in self._sub_page_router:
            ValueError("Cannot include SubPageRouter instance that is already included in this router.")
        if router.parent_sub_page_router is not None:
            ValueError("Cannot include SubPageRouter instance that is already included in another router.")
        if prefix is not Unset:
            router.prefix = prefix
        self._sub_page_router.append(router)
        router._parent_sub_page_router = self

    async def root(self) -> None:
        """
        Root page for this SubPageRouter. This page will be rendered when navigating to the prefix path of this SubPageRouter.

        :return: None
        """

        self.SubPages(self).classes("w-full")

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
            if self.admin.debug:
                title = Unset.resolve(title, error.__class__.__name__)
                message = Unset.resolve(message, error.detail)

        status_code = Unset.resolve(status_code, 500)
        title = Unset.resolve(title, "Internal Server Error")
        icon = Unset.resolve(icon, "error_outline")
        color = Unset.resolve(color, "red")
        message = Unset.resolve(message, "An unexpected error occurred.")

        # ToDo: implement favicon for error pages
        ui.page_title(f"(Debug Mode) - {title}" if self.admin.debug else title)
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
            if self.admin.debug:
                with ui.card().classes("w-400 items-center").props('flat bordered') as card:
                    ui.label(f"(Debug Mode)").classes("text-xl")
                    with ui.grid(columns="1fr 2fr"):
                        ui.label("Router:")
                        ui.link(self.__class__.__name__, target=self.prefix)

                        ui.label("Parent Router:")
                        if self.parent_sub_page_router is not None:
                            ui.link(self.parent_sub_page_router.__class__.__name__, target=self.parent_sub_page_router.prefix)
                        else:
                            ui.label("None")

                        ui.label("SubPages:")
                        with ui.row():
                            for path, kwargs in self.sub_pages.items():
                                ui.link(kwargs["title"], target=path)

                        ui.label("Included SubPageRouters:")
                        with ui.row():
                            for router in self.sub_page_router:
                                ui.link(router.__class__.__name__, target=router.prefix)
            if error is not None and self.admin.debug:
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


class BaseAdmin(SubPageRouter):
    """
    Base class for implementing Admin interface.
    Also the main application class for the SubPage routing system.
    This class should be instantiated and used to include SubPageRouters and define SubPages using the @sub_page decorator or the add_sub_page method.
    """

    def __init__(self,
                 debug: bool | Unset = Unset,
                 prefix: str | Unset = Unset,
                 title: str | Unset = Unset):
        """
        :param debug: Enable debug mode. If True, error pages will display detailed error information and stack traces.
        :param prefix: The path prefix for this SubPageApp. Should start with '/' and should not end with '/'.
        :param title: Admin title.
        """

        SubPageRouter.__init__(self,
                               prefix=Unset.resolve(prefix, "/admin"))

        self.debug: bool = Unset.resolve(debug, False)
        self.title: str = Unset.resolve(title, "Admin")
        self._views: list["BaseView"] = []

        ui.page(f"{self.prefix}/{{_:path}}")(self.root)

    @property
    def prefix(self) -> str:
        """
        Overwritten to make prefix read-only in SubPageApp

        :return: The path prefix for this SubPageApp
        """

        return super().prefix

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
        self.include_sub_page_router(view_instance,
                                     prefix=view_instance.path)

    async def root(self) -> None:
        await super().root()

        dark_mode = ui.dark_mode()

        ui.button("Toggle Dark Mode",
                  on_click=lambda: dark_mode.toggle())
