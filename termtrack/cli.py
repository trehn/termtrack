import curses
from queue import Empty
from threading import Thread

import click
from requests import get

from . import VERSION_STRING
from .body import Earth
from .draw import draw_info, draw_location, draw_map, draw_satellite, draw_satellite_crosshair
from .satellite import EarthSatellite
from .utils.curses import graceful_ctrlc, input_thread_body, setup
from .utils.curses import (
    INPUT_EXIT,
    INPUT_TOGGLE_INFO,
)


@graceful_ctrlc
def render(
        stdscr,
        apsides=False,
        crosshair=False,
        fps=1,
        no_you=False,
        observer=None,
        orbits=0,
        satellite=None,
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
        observer_latitude = None
        observer_longitude = None
        if not no_you:
            location_data = get("http://ip-api.com/json").json()
            observer_latitude = location_data['lat']
            observer_longitude = location_data['lon']
        if observer is not None:
            obs_latlon = observer.split()
            observer_latitude = float(obs_latlon[0])
            observer_longitude = float(obs_latlon[1])
        if satellite is not None:
            satellite_obj = EarthSatellite(satellite, observer_latitude=observer_latitude, observer_longitude=observer_longitude)

        info_panel = False
        while True:
            with curses_lock:
                stdscr.erase()
                body = draw_map(stdscr, body)
                if satellite is not None:
                    satellite_obj.compute()
                    if crosshair:
                        draw_satellite_crosshair(stdscr, body, satellite_obj)
                    draw_satellite(stdscr, body, satellite_obj, apsides=apsides, orbits=orbits)
                if observer_latitude is not None and observer_longitude is not None:
                    draw_location(stdscr, body, observer_latitude, observer_longitude)
                if info_panel and satellite is not None:
                    draw_info(stdscr, satellite_obj)
            try:
                input_action = input_queue.get(True, 1/fps)
            except Empty:
                input_action = None
            if input_action == INPUT_EXIT:
                break
            elif input_action == INPUT_TOGGLE_INFO:
                info_panel = not info_panel
    finally:
        quit_event.set()
        input_thread.join()


def print_version(ctx, param, value):
    if not value or ctx.resilient_parsing:
        return
    click.echo(VERSION_STRING)
    ctx.exit()


@click.command()
@click.option("--apsides", is_flag=True, default=False,
              help="Draw apoapsis and periapsis markers")
@click.option("-c", "--crosshair", is_flag=True, default=False,
              help="Draw crosshair around satellite location")
@click.option("-f", "--fps", default=1, metavar="N",
              help="Frames per second (defaults to 1)")
@click.option("-o", "--orbits", default=0, metavar="N",
              help="Draw this many orbits ahead of the satellite")
@click.option("-O", "--observer", default=None, metavar="'LAT LON'",
              help="Space-separated latitude and longitude of an "
                   "observer; overrides IP-geolocation")
@click.option("-Y", "--no-you", is_flag=True, default=False,
              help="Don't auto-detect your location as observer")
@click.option("--version", is_flag=True, callback=print_version,
              expose_value=False, is_eager=True,
              help="Show version and exit")
@click.argument('satellite', required=False)
def main(**kwargs):
    """
    \b
    Shows a world map tracking SATELLITE. Valid values for SATELLITE are
    numbers from http://www.celestrak.com/NORAD/elements/master.asp (for
    your convenience, "iss" or "tiangong" are also allowed).
    \b
    Hotkeys:
    \ti\tToggle info panels
    \tq\tQuit
    """
    curses.wrapper(render, **kwargs)
