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
    draw_coverage,
    draw_crosshair,
    draw_footprint,
    draw_grid,
    draw_info,
    draw_location,
    draw_map,
    draw_orbits,
    draw_planets,
    draw_satellite,
)
from .layer import Layer, pixel_from_layers
from .satellite import ALIASES, EarthSatellite
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
    INPUT_TOGGLE_COVERAGE,
    INPUT_TOGGLE_CROSSHAIR,
    INPUT_TOGGLE_FOOTPRINT,
    INPUT_TOGGLE_GRID,
    INPUT_TOGGLE_INFO,
    INPUT_TOGGLE_NIGHT,
    INPUT_TOGGLE_ORBIT_APSIDES,
    INPUT_TOGGLE_ORBIT_ASCDESC,
    INPUT_TOGGLE_TOPO,
)
from .utils.text import format_seconds


def check_for_resize(stdscr, body):
    start = datetime.now()
    height, width = stdscr.getmaxyx()

    if body.height != height or body.width != width:
        body = body.__class__(width, height)
        progress_str = "0.0"
        start = datetime.now()
        for progress in body.prepare_map():
            if progress_str != "{:.2f}".format(progress):
                progress_str = "{:.2f}".format(progress)
                elapsed_time = datetime.now() - start
                eta = (elapsed_time / max(progress, 0.01)) * (100 - progress)
                stdscr.erase()
                stdscr.insstr(0, 0, "Rendering map (ETA {}, {}%)...".format(
                    format_seconds(eta.total_seconds()),
                    progress_str,
                ))
                stdscr.refresh()
        return body, True
    else:
        return body, False


def redraw(stdscr, body, layers):
    stdscr.erase()
    for x in range(body.width):
        for y in range(body.height):
            char, color = pixel_from_layers(x, y, layers)
            stdscr.insstr(y, x, char, curses.color_pair(color))


@graceful_ctrlc
def render(
        stdscr,
        apsides=False,
        body="earth",
        coverage=False,
        crosshair=False,
        footprint=False,
        fps=1,
        grid=False,
        info=False,
        me=False,
        night=False,
        observer=None,
        orbit_ascdesc=False,
        orbit_res="/70",
        orbits=0,
        paused=False,
        planets="",
        satellite=None,
        tle=None,
        topo=False,
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
            night = False
            topo = False
            me = False
            satellite = None

        observer_latitude = None
        observer_longitude = None
        if me and observer is None:
            location_data = get("http://ip-api.com/json").json()
            observer_latitude = location_data['lat']
            observer_longitude = location_data['lon']
        if observer is not None:
            obs_latlon = observer.split()
            observer_latitude = float(obs_latlon[0])
            observer_longitude = float(obs_latlon[1])

        time_offset = timedelta(0)
        time = datetime.utcnow() + time_offset
        force_redraw = False

        if paused is True:
            paused = datetime.utcnow()
            force_redraw = True

        if satellite is None and tle is None:
            satellite_obj = None
        else:
            satellite_obj = EarthSatellite(
                satellite,
                time,
                observer_latitude=observer_latitude,
                observer_longitude=observer_longitude,
                tle_file=tle,
            )

        apsides_layer = Layer(draw_apsides, update_timeout=8)
        apsides_layer.hidden = not apsides
        coverage_layer = Layer(draw_coverage, update_timeout=10)
        coverage_layer.hidden = not coverage
        crosshair_layer = Layer(draw_crosshair)
        crosshair_layer.hidden = not crosshair
        footprint_layer = Layer(draw_footprint)
        footprint_layer.hidden = not footprint
        grid_layer = Layer(draw_grid, update_timeout=None)
        grid_layer.hidden = not grid
        info_layer = Layer(draw_info)
        info_layer.hidden = not info
        map_layer = Layer(draw_map, update_timeout=None)
        observer_layer = Layer(draw_location, update_timeout=None)
        orbit_layer = Layer(draw_orbits)
        planet_layer = Layer(draw_planets)
        satellite_layer = Layer(draw_satellite)
        satellite_layer.hidden = satellite_obj is None

        layers = [
            info_layer,
            satellite_layer,
            apsides_layer,
            observer_layer,
            footprint_layer,
            orbit_layer,
            planet_layer,
            coverage_layer,
            map_layer,
            crosshair_layer,
            grid_layer,
        ]

        while True:
            with curses_lock:
                body, did_resize = check_for_resize(stdscr, body)
            if did_resize:
                for layer in layers:
                    layer.last_updated = None

            draw_start = datetime.now()
            if not paused:
                time = datetime.utcnow() + time_offset
            if force_redraw:
                for layer in layers:
                    layer.last_updated = None
            if not paused or force_redraw:
                grid_layer.update(body)
                info_layer.update(
                    body,
                    time,
                    observer_latitude=observer_latitude,
                    observer_longitude=observer_longitude,
                    satellite=satellite_obj,
                )
                map_layer.update(body, time, night=night, topo=topo)
                observer_layer.update(body, observer_latitude, observer_longitude)
                planet_layer.update(body, time, planets)

                if satellite_obj is not None:
                    apsides_layer.update(body, satellite_obj)
                    coverage_layer.update(body, satellite_obj, time)
                    crosshair_layer.update(body, satellite_obj)
                    footprint_layer.update(body, satellite_obj)
                    orbit_layer.update(
                        body,
                        satellite_obj,
                        time,
                        orbits=orbits,
                        orbit_ascdesc=orbit_ascdesc,
                        orbit_resolution=orbit_res,
                    )
                    satellite_layer.update(body, satellite_obj)
                    satellite_obj.compute(time)

                with curses_lock:
                    redraw(stdscr, body, layers)

            draw_time = (datetime.now() - draw_start).total_seconds()

            # get input
            try:
                input_action = input_queue.get(True, max(0, 1/fps - draw_time))
                # we just received an input that probably modified how
                # our screen is supposed to look, ergo we need to redraw
                force_redraw = True
            except Empty:
                input_action = None
                force_redraw = False

            # react to input
            if input_action == INPUT_CYCLE_ORBITS:
                orbits += 1
                orbits = orbits % 4
            elif input_action == INPUT_EXIT:
                break
            elif input_action == INPUT_TIME_MINUS_SHORT:
                if satellite_obj is None:
                    time_offset -= timedelta(minutes=30)
                else:
                    time_offset -= satellite_obj.orbital_period / 20
            elif input_action == INPUT_TIME_MINUS_LONG:
                if satellite_obj is None:
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
                if satellite_obj is None:
                    time_offset += timedelta(minutes=30)
                else:
                    time_offset += satellite_obj.orbital_period / 20
            elif input_action == INPUT_TIME_PLUS_LONG:
                if satellite_obj is None:
                    time_offset += timedelta(hours=6)
                else:
                    time_offset += satellite_obj.orbital_period / 2
            elif input_action == INPUT_TIME_RESET:
                time_offset = timedelta(0)
                if paused:
                    paused = time = datetime.utcnow()
            elif input_action == INPUT_TOGGLE_COVERAGE:
                coverage_layer.hidden = not coverage_layer.hidden
                coverage_layer.last_updated = None
            elif input_action == INPUT_TOGGLE_CROSSHAIR:
                crosshair_layer.hidden = not crosshair_layer.hidden
            elif input_action == INPUT_TOGGLE_FOOTPRINT:
                footprint_layer.hidden = not footprint_layer.hidden
            elif input_action == INPUT_TOGGLE_GRID:
                grid_layer.hidden = not grid_layer.hidden
            elif input_action == INPUT_TOGGLE_INFO:
                info_layer.hidden = not info_layer.hidden
            elif input_action == INPUT_TOGGLE_NIGHT:
                night = not night
                map_layer.last_updated = None
                if night:
                    map_layer.update_timeout = timedelta(seconds=60)
                else:
                    map_layer.update_timeout = None
            elif input_action == INPUT_TOGGLE_ORBIT_APSIDES:
                apsides_layer.hidden = not apsides_layer.hidden
                apsides_layer.last_updated = None
            elif input_action == INPUT_TOGGLE_ORBIT_ASCDESC:
                orbit_ascdesc = not orbit_ascdesc
                orbit_layer.last_updated = None
            elif input_action == INPUT_TOGGLE_TOPO:
                topo = not topo
                map_layer.last_updated = None
    finally:
        quit_event.set()
        input_thread.join()


def print_aliases(ctx, param, value):
    if not value or ctx.resilient_parsing:
        return
    for alias in sorted(ALIASES.keys()):
        click.echo("{}: {}".format(alias, ALIASES[alias]))
    ctx.exit()


def print_version(ctx, param, value):
    if not value or ctx.resilient_parsing:
        return
    click.echo(VERSION_STRING)
    ctx.exit()


@click.command()
@click.option("--aliases", is_flag=True, callback=print_aliases,
              expose_value=False, is_eager=True,
              help="Show all satellite aliases and exit")
@click.option("--apsides", is_flag=True, default=False,
              help="Draw apoapsis and periapsis markers")
@click.option("-b", "--body", default="earth", metavar="BODY",
              help="Which celestial body to draw: Earth, Moon or Mars "
                   "(defaults to Earth)")
@click.option("-c", "--coverage", is_flag=True, default=False,
              help="Show next-orbit coverage overlay")
@click.option("-f", "--footprint", is_flag=True, default=False,
              help="Draw satellite footprint/horizon")
@click.option("--fps", default=1, metavar="N",
              help="Frames per second (defaults to 1)")
@click.option("-g", "--grid", is_flag=True, default=False,
              help="Draw latitude/longitude grid")
@click.option("-i", "--info", is_flag=True, default=False,
              help="Show info panels")
@click.option("-m", "--me", is_flag=True, default=False,
              help="Auto-detect your location as observer")
@click.option("-n", "--night", is_flag=True, default=False,
              help="Shade night side")
@click.option("-o", "--orbits", default=0, metavar="N",
              help="Draw this many orbits ahead of the satellite")
@click.option("--orbit-ascdesc", is_flag=True, default=False,
              help="Draw orbits with ascent/descent markers")
@click.option("-O", "--observer", default=None, metavar="'LAT LON'",
              help="Space-separated latitude and longitude of an "
                   "observer; overrides IP-geolocation")
@click.option("-p", "--paused", is_flag=True, default=False,
              help="Start paused")
@click.option("-P", "--planets", default="", metavar="PLANETS",
              help="Comma-separated list of celestial objects to draw "
                   "(e.g. 'sun,moon')")
@click.option("-r", "--orbit-res", default="/70", metavar="[/]N[+]",
              help="Set distance of orbit markers: 'N' means N minutes, "
                   "'/N' means 1/Nth of orbital period, append a plus "
                   "sign to interpolate in between markers (defaults to /70)")
@click.option("-t", "--topo", is_flag=True, default=False,
              help="Enable coloring of topographical features")
@click.option("--tle", default=None, metavar="FILE",
              help="read TLE data from FILE instead of downloading it "
                   "(SATELLITE will have no effect and can be omitted)")
@click.option("-x", "--crosshair", is_flag=True, default=False,
              help="Draw crosshair around satellite location")
@click.option("--version", is_flag=True, callback=print_version,
              expose_value=False, is_eager=True,
              help="Show version and exit")
@click.argument('satellite', required=False)
def main(**kwargs):
    """
    \b
    Shows a world map tracking SATELLITE. Valid values for SATELLITE are
    numbers from http://www.celestrak.com/NORAD/elements/master.php (for
    your convenience, a number of aliases have been provided).
    \b
    Example satellite aliases (find more with --aliases):
    \thubble\t\tHubble Space Telescope
    \tiss\t\tInternational Space Station
    \b
    Hotkeys:
    \ta\tToggle apsides markers
    \tc\tToggle next-orbit coverage overlay
    \td\tToggle ascent/descent markers
    \tf\tToggle footprint (satellite horizon)
    \tg\tToggle latitude/longitude grid
    \ti\tToggle info panels
    \tn\tToggle night shading
    \to\tCycle through drawing 0-3 next orbits
    \tp\tPause/resume
    \tq\tQuit
    \tr\tReset plotted time to current
    \tt\tToggle topography
    \tx\tToggle crosshair
    \tleft\tSmall step back in time
    \tright\tSmall step forward in time
    \tdown\tLarge step back in time
    \tup\tLarge step forward in time
    """
    curses.wrapper(render, **kwargs)
