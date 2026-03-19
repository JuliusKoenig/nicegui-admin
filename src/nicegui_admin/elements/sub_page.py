import asyncio
from typing import Any, Callable, TYPE_CHECKING

from fastapi import HTTPException
from nicegui import ui, background_tasks
from nicegui.page_arguments import RouteMatch, PageArguments

from nicegui_admin.types import SyncOrAsyncMethod

if TYPE_CHECKING:
    from nicegui_admin.admin import BaseAdmin

class SubPages(ui.sub_pages):
    """
    Custom implementation of the SubPages component that supports both routing to builder functions and including other SubPageRouters as sub-pages.
    The routes are dynamically generated based on the included SubPageRouters and the builder functions decorated with the @sub_page decorator.
    """

    def __init__(self, admin: "BaseAdmin") -> None:
        self.admin: "BaseAdmin" = admin
        super().__init__(show_404=True)

    @property
    def _routes(self) -> dict[str, SyncOrAsyncMethod]:
        """
        The routes for the SubPages component.

        :return: The keys are the paths of the SubPages and the values are the builder functions that should be called when navigating to the corresponding path.
        """

        routes = {}
        for path, kwargs in self.admin.sub_pages.items():
            if self._root_path is not None:
                path = path[len(self._root_path):] if path.startswith(self._root_path) else path
            builder: SyncOrAsyncMethod = kwargs["builder"]
            routes[path] = builder
        return routes

    @property
    def _builder_attributes(self) -> dict[SyncOrAsyncMethod, dict[str, Any]]:
        """
        Builder attributes for the SubPages component.

        :return: The keys are the builder functions and the values are dictionaries containing the attributes of the builders, such as title and icon.
        """

        builder_attributes = {}
        for path, kwargs in self.admin.sub_pages.items():
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
                raise NotImplementedError(f"Favicon for SubPages is not yet supported.")
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
        self.admin.error_page(error=error,
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