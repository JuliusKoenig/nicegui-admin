import random
import string
import logging

from nicegui import ui

from niceguitools.admin.sub_page import SubPageHandler

logger = logging.getLogger(__name__)


def test_menu():
    with ui.header().classes("items-center bg-blue-100"):
        ui.button("Home", on_click=lambda: ui.navigate.to("/")).props("flat")
        ui.button("Test", on_click=lambda: ui.navigate.to(
            f"/test?qwe={''.join(random.choices(string.ascii_letters + string.digits, k=10))}")).props("flat")
        ui.button("Sync Error", on_click=lambda: ui.navigate.to("/sync_error")).props("flat")
        ui.button("Async Error", on_click=lambda: ui.navigate.to("/async_error")).props("flat")
        ui.button("Invalid", on_click=lambda: ui.navigate.to("/invalid")).props("flat")


class MySubPageHandler(SubPageHandler):
    async def root_page(self):
        test_menu()
        self.sub_page_cls()


sub_page_handler = MySubPageHandler()

ui.page("/{_:path}")(sub_page_handler.root_page)


@sub_page_handler.sub_page("/")
def home_page():
    ui.label("Home")


@sub_page_handler.sub_page("/test")
def test(qwe: str = None):
    ui.label("Test")
    ui.label(f"qwe: {qwe}")


@sub_page_handler.sub_page("/sync_error")
def sync_error_page():
    raise RuntimeError("Synchronous error")


@sub_page_handler.sub_page("/async_error", title="Async Error")
async def async_error_page():
    raise RuntimeError("Asynchronous error")


if __name__ in {"__main__", "__mp_main__"}:
    ui.run(port=8000,
           show=False,
           fastapi_docs=True,
           storage_secret="demo_secret_key_change_in_production")
