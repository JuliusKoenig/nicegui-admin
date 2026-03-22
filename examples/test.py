from nicegui import ui

@ui.page("/")
async def index():
    ui.label("Number")
    ui.number()

    ui.label("Input")
    ui.input().props("type='number'")

    dark = ui.dark_mode()
    ui.label('Switch mode:')
    ui.button('Dark', on_click=dark.enable)
    ui.button('Light', on_click=dark.disable)


if __name__ in {"__main__", "__mp_main__"}:
    ui.run(port=8000, show=False, fastapi_docs=True)
