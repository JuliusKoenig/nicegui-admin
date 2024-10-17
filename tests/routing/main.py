#!/usr/bin/env python3
from router import Router

from nicegui import ui


@ui.page('/')  # normal index page (e.g. the entry point of the app)
@ui.page('/{_:path}')  # all other pages will be handled by the router but must be registered to also show the SPA index page
def main():
    router = Router()

    @router.add('/')
    def show_one():
        print('Content One')
        ui.label('Content One').classes('text-2xl')

    @router.add('/two')
    def show_two():
        print('Content Two')
        ui.label('Content Two').classes('text-2xl')

    @router.add('/three')
    def show_three():
        print('Content Three')
        ui.label('Content Three').classes('text-2xl')

    @router.add('/three/sub')
    def show_three_sub():
        print('Content Three Sub')
        ui.label('Content Three Sub').classes('text-2xl')

    # adding some navigation buttons to switch between the different pages
    with ui.row():
        ui.button('One', on_click=lambda: router.open(show_one)).classes('w-32')
        ui.button('Two', on_click=lambda: router.open(show_two)).classes('w-32')
        ui.button('Three', on_click=lambda: router.open(show_three)).classes('w-32')
        ui.button('Three Sub', on_click=lambda: router.open(show_three_sub)).classes('w-32')

    # this places the content which should be displayed
    router.frame().classes('w-full p-4 bg-gray-100')


ui.run()