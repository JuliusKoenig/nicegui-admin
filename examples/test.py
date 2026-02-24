from fastapi import FastAPI
from nicegui import APIRouter, app, ui

my_app = FastAPI()

router = APIRouter()


@router.page("/")
async def index():
    ui.label("Hello World!")


my_app.include_router(router)

app.mount("/admin", my_app)

if __name__ in {"__main__", "__mp_main__"}:
    ui.run(port=8000, show=False, fastapi_docs=True)
