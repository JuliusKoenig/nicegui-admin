from nicegui import ui

@ui.page("/")
async def index():
    test = ui.input()
    test.props("type='textarea'")
    test.prefix = "Test"
    ui.label("Value")
    ui.label().bind_text_from(test, "value")

    dark = ui.dark_mode()
    ui.label('Switch mode:')
    ui.button('Dark', on_click=dark.enable)
    ui.button('Light', on_click=dark.disable)


if __name__ in {"__main__", "__mp_main__"}:
    ui.run(port=8000, show=False, fastapi_docs=True)
