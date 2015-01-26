import curses
from queue import Empty
from threading import Thread

import click
from requests import get

from . import VERSION_STRING
from .body import Earth
from .draw import draw_location, draw_map, draw_satellite
from .satellite import EarthSatellite
from .utils.curses import graceful_ctrlc, input_thread_body, setup
from .utils.curses import INPUT_EXIT


@graceful_ctrlc
def render(
        stdscr,
        fps=1,
        no_you=False,
        **kwargs
    ):
    curses_lock, input_queue, quit_event = setup(stdscr)
    input_thread = Thread(
        args=(stdscr, input_queue, quit_event, curses_lock),
        target=input_thread_body,
    )
    input_thread.start()
    try:
        body = Earth(1, 1)
        iss = EarthSatellite(25544)
        while True:
            with curses_lock:
                stdscr.erase()
                body = draw_map(stdscr, body)
                draw_satellite(stdscr, body, iss)
                if not no_you:
                    location_data = get("http://ip-api.com/json").json()
                    draw_location(stdscr, body, location_data['lat'], location_data['lon'])
            try:
                input_action = input_queue.get(True, 1/fps)
            except Empty:
                input_action = None
            if input_action == INPUT_EXIT:
                break
    finally:
        quit_event.set()
        input_thread.join()


def print_version(ctx, param, value):
    if not value or ctx.resilient_parsing:
        return
    click.echo(VERSION_STRING)
    ctx.exit()


@click.command()
@click.option("-f", "--fps", default=1, metavar="N",
              help="Frames per second (defaults to 1)")
@click.option("-Y", "--no-you", is_flag=True, default=False)
@click.option("--version", is_flag=True, callback=print_version,
              expose_value=False, is_eager=True,
              help="Show version and exit")
def main(**kwargs):
    curses.wrapper(render, **kwargs)
