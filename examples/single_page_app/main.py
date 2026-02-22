from starlette.requests import Request

from custom_sub_pages import custom_sub_pages

from nicegui import ui


@ui.page("/")
@ui.page("/{_:path}")
def main_page(request: Request):
    with ui.header().classes("items-center bg-blue-100"):
        ui.button("Home", on_click=lambda: ui.navigate.to("/")).props("flat")
        ui.button("Test", on_click=lambda: ui.navigate.to("/test")).props("flat")
        ui.button("Sync Error", on_click=lambda: ui.navigate.to("/sync_error")).props("flat")
        ui.button("Async Error", on_click=lambda: ui.navigate.to("/async_error")).props("flat")
        ui.button("Invalid", on_click=lambda: ui.navigate.to("/invalid")).props("flat")

    custom_sub_pages({"/": home,
                      "/test": test,
                      "/test/{qwe}": test,
                      "/sync_error": sync_error_page,
                      "/async_error": async_error_page, },
                     show_404=True).classes("flex-grow p-4")


def home():
    ui.page_title("Home")
    ui.label("Home")


def test(qwe: str = None):
    ui.page_title("Test")
    ui.label("Test")
    ui.label(f"qwe: {qwe}")


def sync_error_page():
    raise RuntimeError("Synchronous error")


async def async_error_page():
    raise RuntimeError("Asynchronous error")


if __name__ in {'__main__', '__mp_main__'}:
    ui.run(port=8000, show=False, fastapi_docs=True, storage_secret='demo_secret_key_change_in_production')
