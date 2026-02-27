from nicegui import app
from nicegui import ui

from nicegui_admin.sub_page import SubPageApp, subpage, SubPageRouter


class MyApp(SubPageApp):
    @subpage(path="/class_page_app")
    def class_page_app(self):
        ui.label("This is the 'class_page_app' sub page")


my_app = MyApp(debug=True, prefix="/admin")


@my_app.subpage("/page_app")
def page_app():
    ui.label("This is the 'page_app' sub page")


class MyRouter(SubPageRouter):
    @subpage(path="/class_page_router")
    def class_page_router(self):
        ui.label("This is the 'class_page_router' sub page")


my_router = MyRouter(prefix="/my_router")


@my_router.subpage("/page_router")
def page_router():
    ui.label("This is the 'page_router' sub page")


my_app.include_subpage_router(my_router)

app.include_router(my_app)


@ui.page("/")
def index():
    ui.label("This is the main page")
    ui.link("Go to sub page", "/admin")


if __name__ in {"__main__", "__mp_main__"}:
    ui.run(port=8000, show=False, fastapi_docs=True)
