#!/usr/bin/env python3

import curses
from copy import copy
from datetime import datetime, timedelta
from math import pi
from os.path import expanduser
from queue import Empty, Queue
import re
import shelve
from threading import Event, Lock, Thread
from time import sleep

import click
import ephem
import requests
import shapefile

INPUT_EXIT = 1

MAP_CACHE = "~/.termtrack_map_cache"


def rad_to_deg(value):
    return value * 180 / pi


class EarthSatellite(object):
    def __init__(self, number):
        raw_html = requests.get("http://www.celestrak.com/cgi-bin/TLE.pl?CATNR={}".format(number)).text
        r = re.compile("PRE>(.*)</PRE", flags=re.DOTALL)
        tle = r.search(raw_html).group(1).strip().split("\n")
        self._satellite = ephem.readtle(*tle)

    def latlon(self, plus_minutes=0):
        self._satellite.compute(datetime.utcnow() + timedelta(minutes=plus_minutes))
        return rad_to_deg(self._satellite.sublat), rad_to_deg(self._satellite.sublong)


class Body(object):
    def __init__(self, width, height):
        self.height = height
        self.width = width
        self.lat_range = self.LAT_MAX - self.LAT_MIN
        self.lon_range = self.LON_MAX - self.LON_MIN
        self.pixel_percentage = 100 / (self.width * self.height)
        self._sf = shapefile.Reader(self.SHAPEFILE)

    def from_latlon(self, lat, lon):
        if (
            lat > self.LAT_MAX or
            lat < self.LAT_MIN or
            lon > self.LON_MAX or
            lon < self.LON_MIN
        ):
            raise ValueError()
        xrel = (lon - self.LON_MIN) / self.lon_range
        yrel = (self.LAT_MAX - lat) / self.lat_range
        x = int(round(self.width * xrel))
        y = int(round(self.height * yrel))
        return min(x, self.width-1), min(y, self.height)

    def prepare_map(self):
        map_cache = shelve.open(expanduser(MAP_CACHE))
        try:
            map_cache_key = "{}_{}x{}".format(self.NAME, self.width, self.height)
            if map_cache_key in map_cache:
                self.map = map_cache[map_cache_key]
                raise StopIteration()
            progress = 0.0
            empty_line = [None for i in range(self.height)]
            self.map = [copy(empty_line) for i in range(self.width-1)]
            for x in range(self.width-1):
                for y in range(self.height):
                    yield progress
                    lat, lon = self.to_latlon(x, y)
                    land = False
                    for shape in self._sf.shapes():
                        if (
                            # for performance reasons we quickly check the
                            # bounding box before trying the more expensive
                            # point_in_poly() call
                            lat > shape.bbox[1] and
                            lat < shape.bbox[3] and
                            lon > shape.bbox[0] and
                            lon < shape.bbox[2]
                        ) and point_in_poly(lon, lat, shape.points):
                            land = True
                            break
                    if land:
                        self.map[x][y] = True
                    else:
                        self.map[x][y] = False
                    progress += self.pixel_percentage
                    yield progress
            map_cache[map_cache_key] = self.map
        finally:
            map_cache.close()

    def to_latlon(self, x, y):
        xrel = x / self.width
        yrel = y / self.height
        return (
            self.LAT_MAX - yrel * self.lat_range,
            self.LON_MIN + xrel * self.lon_range,
        )


class Earth(Body):
    LON_MIN = -180
    LON_MAX = 180
    LAT_MIN = -60
    LAT_MAX = 85
    NAME = "Earth"
    SHAPEFILE = "ne_110m_land.shp"


def point_in_poly(x, y, poly):
    n = len(poly)
    inside = False
    p1x, p1y = poly[0]
    for i in range(n+1):
        p2x, p2y = poly[i % n]
        if y > min(p1y, p2y):
            if y <= max(p1y, p2y):
                if x <= max(p1x, p2x):
                    if p1y != p2y:
                        xints = (y-p1y) * (p2x-p1x) / (p2y-p1y) + p1x
                    if p1x == p2x or x <= xints:
                        inside = not inside
        p1x, p1y = p2x, p2y
    return inside


def log(msg):
    with open("log", "a") as f:
        f.write(msg)


def draw_map(stdscr, body):
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
                stdscr.addstr(0, 0, "Rendering map (ETA {}s, {}%)...".format(int(eta.total_seconds()), progress_str))
                stdscr.refresh()
    for x in range(width-1):
        for y in range(height):
            sun = ephem.Sun()
            obs = ephem.Observer()
            obs.pressure = 0
            lat, lon = body.to_latlon(x, y)
            obs.lat = "{:.8f}".format(lat)
            obs.lon = "{:.8f}".format(lon)
            sun.compute(obs)
            if sun.alt > 0:
                color = 1
            else:
                color = 2
            if body.map[x][y]:
                stdscr.addstr(y, x, "•", curses.color_pair(color))
            else:
                stdscr.addstr(y, x, " ", curses.color_pair(color))
    return body


def draw_satellite(stdscr, body, satellite):
    for i in range(270):
        x, y = body.from_latlon(*satellite.latlon(plus_minutes=i))
        stdscr.addstr(y, x, "#", curses.color_pair(4))


def draw_location(stdscr, body, lat, lon):
    x, y = body.from_latlon(lat, lon)
    stdscr.addstr(y, x, "•", curses.color_pair(3))


def setup(stdscr):
    # curses
    curses.use_default_colors()
    curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLACK)
    curses.init_pair(2, curses.COLOR_BLUE, curses.COLOR_BLACK)
    curses.init_pair(3, curses.COLOR_RED, curses.COLOR_BLACK)
    curses.init_pair(4, curses.COLOR_WHITE, curses.COLOR_BLACK)
    curses.curs_set(False)
    stdscr.timeout(0)

    # prepare input thread mechanisms
    curses_lock = Lock()
    input_queue = Queue()
    quit_event = Event()
    return (curses_lock, input_queue, quit_event)


def graceful_ctrlc(func):
    """
    Makes the decorated function terminate silently on CTRL+C.
    """
    def wrapper(*args, **kwargs):
        try:
            func(*args, **kwargs)
        except KeyboardInterrupt:
            pass
    return wrapper


def input_thread_body(stdscr, input_queue, quit_event, curses_lock):
    while not quit_event.is_set():
        try:
            with curses_lock:
                key = stdscr.getkey()
        except:
            key = None
        if key in ("q", "Q"):
            input_queue.put(INPUT_EXIT)
        sleep(0.01)


def print_version(ctx, param, value):
    if not value or ctx.resilient_parsing:
        return
    click.echo(VERSION)
    ctx.exit()


@graceful_ctrlc
def render(
        stdscr,
        fps=1,
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
            try:
                input_action = input_queue.get(True, 1/fps)
            except Empty:
                input_action = None
            if input_action == INPUT_EXIT:
                break
    finally:
        quit_event.set()
        input_thread.join()


@click.command()
@click.option("-f", "--fps", default=1, metavar="N",
              help="Frames per second (defaults to 1)")
@click.option("--version", is_flag=True, callback=print_version,
              expose_value=False, is_eager=True,
              help="Show version and exit")
def main(**kwargs):
    curses.wrapper(render, **kwargs)


if __name__ == '__main__':
    main()
