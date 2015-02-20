import curses
from datetime import datetime, timedelta
from queue import Empty
from threading import Thread

import click
from requests import get

from . import VERSION_STRING
from .body import BODY_MAP
from .draw import (
    draw_apsides,
    draw_footprint,
    draw_grid,
    draw_info,
    draw_location,
    draw_map,
    draw_orbits,
    draw_satellite,
    draw_satellite_crosshair,
)
from .satellite import EarthSatellite
from .utils.curses import graceful_ctrlc, input_thread_body, setup
from .utils.curses import (
    INPUT_CYCLE_ORBITS,
    INPUT_EXIT,
    INPUT_TIME_MINUS_LONG,
    INPUT_TIME_MINUS_SHORT,
    INPUT_TIME_PAUSE,
    INPUT_TIME_PLUS_LONG,
    INPUT_TIME_PLUS_SHORT,
    INPUT_TIME_RESET,
    INPUT_TOGGLE_CROSSHAIR,
    INPUT_TOGGLE_FOOTPRINT,
    INPUT_TOGGLE_GRID,
    INPUT_TOGGLE_INFO,
    INPUT_TOGGLE_ORBIT_APSIDES,
    INPUT_TOGGLE_ORBIT_ASCDESC,
)


@graceful_ctrlc
def render(
        stdscr,
        apsides=False,
        body="earth",
        crosshair=False,
        footprint=False,
        fps=1,
        grid=False,
        no_night=False,
        no_topo=False,
        no_you=False,
        observer=None,
        orbit_ascdesc=False,
        orbit_res="/70",
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
        body = BODY_MAP[body.lower()](1, 1)
        if body.NAME != "Earth":
            no_night = True
            no_topo = False
            no_you = True
            satellite = None

        observer_latitude = None
        observer_longitude = None
        if not no_you and observer is None:
            location_data = get("http://ip-api.com/json").json()
            observer_latitude = location_data['lat']
            observer_longitude = location_data['lon']
        if observer is not None:
            obs_latlon = observer.split()
            observer_latitude = float(obs_latlon[0])
            observer_longitude = float(obs_latlon[1])

        info_panel = False
        paused = False
        time_offset = timedelta(0)
        time = datetime.utcnow() + time_offset
        force_redraw_while_paused = False

        if satellite is None:
            satellite_obj = None
        else:
            satellite_obj = EarthSatellite(satellite, time, observer_latitude=observer_latitude, observer_longitude=observer_longitude)

        while True:
            if not paused:
                time = datetime.utcnow() + time_offset
            if not paused or force_redraw_while_paused:
                with curses_lock:
                    stdscr.erase()
                    body = draw_map(stdscr, body, time, night=not no_night, topo=not no_topo)
                    if grid:
                        draw_grid(stdscr, body)
                    if satellite is not None:
                        satellite_obj.compute(time)
                        if crosshair:
                            draw_satellite_crosshair(stdscr, body, satellite_obj)
                        if footprint:
                            draw_footprint(stdscr, body, satellite_obj)
                        if orbits > 0:
                            draw_orbits(
                                stdscr,
                                body,
                                satellite_obj,
                                time,
                                orbits=orbits,
                                orbit_ascdesc=orbit_ascdesc,
                                orbit_resolution=orbit_res,
                            )
                        if apsides:
                            draw_apsides(stdscr, body, satellite_obj)
                        draw_satellite(stdscr, body, satellite_obj)
                    if observer_latitude is not None and observer_longitude is not None:
                        draw_location(stdscr, body, observer_latitude, observer_longitude)
                    if info_panel and satellite is not None:
                        draw_info(
                            stdscr,
                            time,
                            observer_latitude=observer_latitude,
                            observer_longitude=observer_longitude,
                            satellite=satellite_obj,
                        )

            # get input
            try:
                input_action = input_queue.get(True, 1/fps)
                # we just received an input that probably modified how
                # our screen is supposed to look, ergo we need to redraw
                force_redraw_while_paused = True
            except Empty:
                input_action = None
                force_redraw_while_paused = False

            # react to input
            if input_action == INPUT_CYCLE_ORBITS:
                orbits += 1
                orbits = orbits % 4
            elif input_action == INPUT_EXIT:
                break
            elif input_action == INPUT_TIME_MINUS_SHORT:
                if satellite is None:
                    time_offset -= timedelta(minutes=30)
                else:
                    time_offset -= satellite_obj.orbital_period / 20
            elif input_action == INPUT_TIME_MINUS_LONG:
                if satellite is None:
                    time_offset -= timedelta(hours=6)
                else:
                    time_offset -= satellite_obj.orbital_period / 2
            elif input_action == INPUT_TIME_PAUSE:
                if paused:
                    time_offset -= datetime.utcnow() - paused
                    paused = False
                else:
                    paused = datetime.utcnow()
            elif input_action == INPUT_TIME_PLUS_SHORT:
                if satellite is None:
                    time_offset += timedelta(minutes=30)
                else:
                    time_offset += satellite_obj.orbital_period / 20
            elif input_action == INPUT_TIME_PLUS_LONG:
                if satellite is None:
                    time_offset += timedelta(hours=6)
                else:
                    time_offset += satellite_obj.orbital_period / 2
            elif input_action == INPUT_TIME_RESET:
                time_offset = timedelta(0)
            elif input_action == INPUT_TOGGLE_CROSSHAIR:
                crosshair = not crosshair
            elif input_action == INPUT_TOGGLE_FOOTPRINT:
                footprint = not footprint
            elif input_action == INPUT_TOGGLE_GRID:
                grid = not grid
            elif input_action == INPUT_TOGGLE_INFO:
                info_panel = not info_panel
            elif input_action == INPUT_TOGGLE_ORBIT_APSIDES:
                apsides = not apsides
            elif input_action == INPUT_TOGGLE_ORBIT_ASCDESC:
                orbit_ascdesc = not orbit_ascdesc
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
@click.option("-b", "--body", default="earth", metavar="BODY",
              help="Which celestial body to draw: Earth, Moon or Mars "
                   "(defaults to Earth)")
@click.option("-c", "--crosshair", is_flag=True, default=False,
              help="Draw crosshair around satellite location")
@click.option("-f", "--footprint", is_flag=True, default=False,
              help="Draw satellite footprint/horizon")
@click.option("--fps", default=1, metavar="N",
              help="Frames per second (defaults to 1)")
@click.option("-g", "--grid", is_flag=True, default=False,
              help="Draw latitude/longitude grid")
@click.option("-N", "--no-night", is_flag=True, default=False,
              help="Don't shade night side")
@click.option("-o", "--orbits", default=0, metavar="N",
              help="Draw this many orbits ahead of the satellite")
@click.option("--orbit-ascdesc", is_flag=True, default=False,
              help="Draw orbits with ascent/descent markers")
@click.option("-O", "--observer", default=None, metavar="'LAT LON'",
              help="Space-separated latitude and longitude of an "
                   "observer; overrides IP-geolocation")
@click.option("-r", "--orbit-res", default="/70", metavar="[/]N",
              help="Set distance of orbit markers: 'N' means N minutes, "
                   "'/N' means 1/Nth of orbital period (defaults to /70)")
@click.option("-T", "--no-topo", is_flag=True, default=False,
              help="Disable rendering of topographical features")
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
    your convenience, the aliases listed below are also allowed).
    \b
    Satellite aliases:
    \thubble\t\tHubble Space Telescope
    \tiss\t\tInternational Space Station
    \ttiangong\tTiangong-1 (Chinese space station)
    \b
    Hotkeys:
    \ta\tToggle apsides markers
    \tc\tToggle crosshair
    \td\tToggle ascent/descent markers
    \tf\tToggle footprint (satellite horizon)
    \tg\tToggle latitude/longitude grid
    \ti\tToggle info panels
    \to\tCycle through drawing 0-3 next orbits
    \tp\tPause/resume
    \tq\tQuit
    \tr\tReset plotted time to current
    \tleft\tSmall step back in time
    \tright\tSmall step forward in time
    \tdown\tLarge step back in time
    \tup\tLarge step forward in time
    """
    curses.wrapper(render, **kwargs)
