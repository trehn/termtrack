import curses
from datetime import datetime, timedelta

import ephem

from .utils.text import format_seconds


def draw_info(stdscr, satellite, right=True):
    height, width = stdscr.getmaxyx()
    lat, lon = satellite.latlon()
    text = []
    text.append(satellite.name)
    text.append("")
    text.append("Latitude:")
    text.append("  {:.6f}".format(lat))
    text.append("")
    text.append("Longitude:")
    text.append("  {:.6f}".format(lon))
    text.append("")
    text.append("Inclination:")
    text.append("  {:.4f}°".format(satellite.inclination))
    text.append("")
    text.append("Orbital period:")
    text.append("  " + format_seconds(satellite.orbital_period.total_seconds()))

    longest_line = max(map(len, text))

    padded_lines = []
    for line in text:
        padded_lines.append("┃ " + line.ljust(longest_line+1) + "┃")
    padded_lines.insert(0, "╭" + "─" * (longest_line+2) + "╮")
    padded_lines.append("╰" + "─" * (longest_line+2) + "╯")

    if right:
        x = width - len(padded_lines[0]) - 2
    else:
        x = 2
    y = 1

    if len(padded_lines)+1 <= height and len(padded_lines[0]) + 2 <= width:
        for line in padded_lines:
            stdscr.addstr(y, x, line)
            y += 1


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
                stdscr.addstr(0, 0, "Rendering map (ETA {}s, {}%)...".format(
                    int(eta.total_seconds()),
                    progress_str,
                ))
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
                color = 48
            elif sun.alt > -0.05:
                color = 37
            elif sun.alt > -0.1:
                color = 33
            elif sun.alt > -0.2:
                color = 28
            else:
                color = 22
            if body.map[x][y]:
                stdscr.addstr(y, x, "•", curses.color_pair(color))
            else:
                stdscr.addstr(y, x, " ", curses.color_pair(color))
    return body


def draw_satellite(stdscr, body, satellite, orbits=0):
    orbit_offset = timedelta()
    while orbit_offset < satellite.orbital_period * orbits:
        orbit_offset += satellite.orbital_period / 80
        try:
            x, y = body.from_latlon(*satellite.latlon(plus_seconds=orbit_offset.total_seconds()))
            stdscr.addstr(y, x, "•", curses.color_pair(167))
        except ValueError:
            pass
        except:
            raise ValueError("{}x{} {}".format(x, y, stdscr.getmaxyx()))

    try:
        x, y = body.from_latlon(*satellite.latlon())
        stdscr.addstr(y, x, "X", curses.color_pair(16))
    except ValueError:
        pass

def draw_location(stdscr, body, lat, lon):
    x, y = body.from_latlon(lat, lon)
    stdscr.addstr(y, x, "•", curses.color_pair(2))
