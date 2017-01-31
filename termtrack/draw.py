from datetime import timedelta
from math import acos, cos, degrees, radians, sin

import ephem

from .planets import PLANET_SYMBOLS, latlon_for_planet
from .satellite import earth_radius_at_latitude
from .utils.curses import bresenham, closest_color, fill_outline
from .utils.geometry import (
    cartesian_to_latlon,
    latlon_to_cartesian,
    latlon_to_spherical,
    spherical_to_cartesian,
)
from .utils.text import format_seconds


GRID_LATITUDES = (60, 30, 0, -30, -60)
GRID_LONGITUDES = (150, 120, 90, 60, 30, 0, -30, -60, -90, -120, -150)


class InfoPanel(list):
    pass


def draw_coverage(layer, body, satellite, time, steps=100):
    interval = satellite.orbital_period.total_seconds() / steps
    footprints = set([])

    for i in range(steps):
        satellite.compute(time, plus_seconds=interval * i)
        earth_radius = earth_radius_at_latitude(satellite.latitude)
        horizon_radius = acos(earth_radius / (earth_radius + satellite.altitude))
        sat_xy = body.from_latlon(satellite.latitude, satellite.longitude)
        sat_footprints = []

        for hx, hy, hz in cartesian_rotation(
            satellite.latitude,
            satellite.longitude,
            horizon_radius,
            steps=int(body.width / 4),  # somewhat arbitrary
        ):
            sat_footprints.append(body.from_latlon(*cartesian_to_latlon(hx, hy, hz)))

        sat_outline = set(bresenham(sat_footprints, body.width, body.height, connect_ends=True))
        fill_outline(sat_xy, sat_outline, body.width, body.height)
        footprints.update(sat_outline)

    # now we have gathered the swept area, but we want to hide areas
    # *not* covered during the orbit
    inverted_footprints = []
    for x in range(body.width):
        for y in range(body.height):
            if (x, y) not in footprints:
                inverted_footprints.append((x, y))

    for x, y in inverted_footprints:
        layer.draw(x, y, "•", 94)

    # reset satellite to current position
    satellite.compute(time)


def draw_grid(layer, body):
    latitudes = []
    longitudes = []
    for lat in GRID_LATITUDES:
        x, y = body.from_latlon(lat, 0)
        latitudes.append(y)
    for lon in GRID_LONGITUDES:
        x, y = body.from_latlon(0, lon)
        longitudes.append(x)

    for x in range(body.width-1):
        for y in range(body.height):
            if body.map[x][y][3] is None:
                if x in longitudes and y in latitudes:
                    layer.draw(x, y, "┼", 234)
                elif x in longitudes:
                    layer.draw(x, y, "│", 234)
                elif y in latitudes:
                    layer.draw(x, y, "─", 234)


def draw_info(
    layer,
    body,
    time,
    observer_latitude=None,
    observer_longitude=None,
    satellite=None,
):
    if satellite is not None:
        text_basic = InfoPanel()
        text_basic.append(satellite.name)
        text_basic.append("---")
        text_basic.append("Latitude:")
        text_basic.append("  {:.6f}°".format(satellite.latitude))
        text_basic.append("")
        text_basic.append("Longitude:")
        text_basic.append("  {:.6f}°".format(satellite.longitude))
        text_basic.append("")
        text_basic.append("Altitude:")
        text_basic.append("  {:,.2f}km".format(satellite.altitude / 1000))
        text_basic.append("")
        text_basic.append("Velocity:")
        text_basic.append("  {:,.2f}m/s".format(satellite.velocity))
        text_basic.append("")
        text_basic.append("Orbital period:")
        text_basic.append("  " + format_seconds(satellite.orbital_period.total_seconds()))
        text_basic.top = True
        text_basic.left = True

        text_apsides = InfoPanel()
        text_apsides.append("Apogee altitude:")
        text_apsides.append("  {:,.2f}km".format(satellite.apoapsis_altitude / 1000))
        text_apsides.append("")
        text_apsides.append("Perigee altitude:")
        text_apsides.append("  {:,.2f}km".format(satellite.periapsis_altitude / 1000))
        text_apsides.append("")
        text_apsides.append("Time to perigee:")
        text_apsides.append("  " + format_seconds(satellite.time_to_periapsis.total_seconds()))
        text_apsides.append("")
        text_apsides.append("Time since perigee:")
        text_apsides.append("  " + format_seconds(satellite.time_since_periapsis.total_seconds()))
        text_apsides.append("")
        text_apsides.append("Time to apogee:")
        text_apsides.append("  " + format_seconds(satellite.time_to_apoapsis.total_seconds()))
        text_apsides.append("")
        text_apsides.append("Time since apogee:")
        text_apsides.append("  " + format_seconds(satellite.time_since_apoapsis.total_seconds()))
        text_apsides.top = False
        text_apsides.left = False

        text_params = InfoPanel()
        text_params.append("Inclination:")
        text_params.append("  {:.4f}°".format(degrees(satellite.inclination)))
        text_params.append("")
        text_params.append("RA of asc node:")
        text_params.append("  {:.4f}°".format(
            degrees(satellite.right_ascension_of_ascending_node)
        ))
        text_params.append("")
        text_params.append("Arg of periapsis:")
        text_params.append("  {:.4f}°".format(degrees(satellite.argument_of_periapsis)))
        text_params.append("")
        text_params.append("Eccentricity:")
        text_params.append("  {:.7f}".format(satellite.eccentricity))
        text_params.append("")
        text_params.append("Semi-major axis:")
        text_params.append("  {:,.2f}km".format(satellite.semi_major_axis / 1000))
        text_params.append("")
        text_params.append("Mean anomaly @epoch:")
        text_params.append("  {:.4f}°".format(degrees(satellite.mean_anomaly_at_epoch)))
        text_params.append("")
        text_params.append("Epoch (UTC):")
        text_params.append(satellite.epoch.strftime("  %Y-%m-%d %H:%M:%S"))
        text_params.append("")
        text_params.append("Current time (UTC):")
        text_params.append(time.strftime("  %Y-%m-%d %H:%M:%S"))
        text_params.top = False
        text_params.left = True

        panels = [text_params, text_apsides, text_basic]

    else:  # no satellite
        text_time = InfoPanel()
        text_time.append("Time (UTC):")
        text_time.append(time.strftime("  %Y-%m-%d %H:%M:%S"))
        text_time.top = False
        text_time.left = True

        panels = [text_time]

    if observer_latitude is not None and observer_longitude is not None:
        text_observer = InfoPanel()
        text_observer.append("Observer")
        text_observer.append("---")
        text_observer.append("Latitude:")
        text_observer.append("  {:.6f}°".format(observer_latitude))
        text_observer.append("")
        text_observer.append("Longitude:")
        text_observer.append("  {:.6f}°".format(observer_longitude))
        if satellite is not None:
            text_observer.append("")
            text_observer.append("Azimuth:")
            text_observer.append("  {:.2f}°".format(degrees(satellite.observer_azimuth)))
            text_observer.append("")
            text_observer.append("Altitude:")
            text_observer.append("  {:.2f}°".format(degrees(satellite.observer_altitude)))
            if satellite.acquisition_of_signal is not None and \
                    satellite.loss_of_signal is not None:
                text_observer.append("")
                text_observer.append("AOS:")
                text_observer.append("  {}".format(
                    format_seconds((
                        satellite.acquisition_of_signal.datetime() - time
                    ).total_seconds())
                ))
                text_observer.append("")
                text_observer.append("LOS:")
                text_observer.append("  {}".format(
                    format_seconds((
                        satellite.loss_of_signal.datetime() - time
                    ).total_seconds())
                ))
        text_observer.top = True
        text_observer.left = False
        panels.append(text_observer)

    for text in panels:
        longest_line = max(map(len, text))

        text.padded_lines = []
        for line in text:
            if line == "---":
                text.padded_lines.append("├" + "─" * (longest_line+2) + "┤")
            else:
                text.padded_lines.append("│ " + line.ljust(longest_line+1) + "│")
        text.padded_lines.insert(0, "╭" + "─" * (longest_line+2) + "╮")
        text.padded_lines.append("╰" + "─" * (longest_line+2) + "╯")

        if text.left:
            text.x = 2
        else:
            text.x = body.width - len(text.padded_lines[0]) - 2
        if text.top:
            text.y = 1
        else:
            text.y = body.height - len(text.padded_lines) - 1

        for y, line in enumerate(text.padded_lines):
            for x, char in enumerate(line):
                layer.draw(text.x + x, text.y + y, char, 0)


def draw_map(layer, body, time, night=True, topo=True):
    for x in range(body.width):
        for y in range(body.height):
            if night:
                sun = ephem.Sun()
                obs = ephem.Observer()
                obs.pressure = 0
                lat, lon = body.to_latlon(x, y)
                obs.lat = "{:.8f}".format(lat)
                obs.lon = "{:.8f}".format(lon)
                obs.date = time
                sun.compute(obs)
                # astronomical twilight starts at -18°
                # -0.3141592 = radians(-18)
                night_factor = max(min(sun.alt, 0), -0.3141592) / -0.3141592
            else:
                night_factor = -1

            if body.map[x][y][3] is not None:
                if topo is True:
                    r, g, b, color = body.map[x][y][:4]
                else:
                    r, g, b, color = 0, 249, 114, 48
                if night_factor > -0.001:
                    night_r = 0
                    night_g = g * 0.2
                    night_b = min(b + 40, 255)
                    effective_r = ((1 - night_factor) * r) + (night_factor * night_r)
                    effective_g = ((1 - night_factor) * g) + (night_factor * night_g)
                    effective_b = ((1 - night_factor) * b) + (night_factor * night_b)
                    color = closest_color(effective_r, effective_g, effective_b)
                layer.draw(x, y, "•", color)


def draw_orbits(
    layer,
    body,
    satellite,
    time,
    orbit_ascdesc=False,
    orbits=0,
    orbit_resolution="/70",
):
    if orbits == 0:
        return
    orbit_offset = timedelta()
    continuous = False
    if orbit_resolution.endswith("+"):
        continuous = True
        orbit_resolution = orbit_resolution.rstrip("+")
    if orbit_resolution.startswith("/"):
        orbit_increment = satellite.orbital_period / int(orbit_resolution[1:])
    else:
        orbit_increment = timedelta(minutes=float(orbit_resolution))

    satellite.compute(time)
    previous_altitude = satellite.altitude

    orbit_markers = []

    while orbit_offset < satellite.orbital_period * orbits + orbit_increment:
        satellite.compute(time, plus_seconds=orbit_offset.total_seconds())

        if orbit_ascdesc:
            if satellite.altitude - previous_altitude >= 0:
                char = "+"
            else:
                char = "-"
            previous_altitude = satellite.altitude
        else:
            char = "•"

        orbit_markers.append((body.from_latlon(satellite.latitude, satellite.longitude), char))
        orbit_offset += orbit_increment

    if continuous:
        orbit_marker_dict = dict(orbit_markers)
        orbit_markers = bresenham(
            [point for point, char in orbit_markers],
            body.width,
            body.height,
        )
        char = "•"
        for x, y in orbit_markers:
            try:
                char = orbit_marker_dict[(x, y)]
                interpolated = False
            except KeyError:
                interpolated = True
            color = 131 if interpolated else 209
            layer.draw(x, y, char, color)
    else:
        for point, char in orbit_markers:
            layer.draw(point[0], point[1], char, 209)

    # reset values to current
    satellite.compute(time)


def draw_planets(layer, body, time, planets):
    for planet in planets.split(","):
        planet = planet.strip().lower()
        if not planet:
            continue
        symbol = PLANET_SYMBOLS[planet]
        lat, lon = latlon_for_planet(planet, time)
        x, y = body.from_latlon(lat, lon)
        layer.draw(x, y, symbol, 227)


def draw_apsides(layer, body, satellite):
    try:
        x, y = body.from_latlon(satellite.apoapsis_latitude, satellite.apoapsis_longitude)
        layer.draw(x, y, "A", 167)
    except ValueError:
        pass
    try:
        x, y = body.from_latlon(satellite.periapsis_latitude, satellite.periapsis_longitude)
        layer.draw(x, y, "P", 167)
    except ValueError:
        pass


def draw_footprint(layer, body, satellite):
    earth_radius = earth_radius_at_latitude(satellite.latitude)
    horizon_radius = acos(earth_radius / (earth_radius + satellite.altitude))
    footprint_markers = []

    for hx, hy, hz in cartesian_rotation(
        satellite.latitude,
        satellite.longitude,
        horizon_radius,
        steps=int(body.width / 4),  # somewhat arbitrary
    ):
        footprint_markers.append(body.from_latlon(*cartesian_to_latlon(hx, hy, hz)))

    footprint_markers = bresenham(footprint_markers, body.width, body.height, connect_ends=True)

    for x, y in footprint_markers:
        layer.draw(x, y, "•", 239)


def cartesian_rotation(lat, lon, r, steps=128):
    """
    Internally converts to Cartesian coordinates and applies a rotation
    matrix to yield a number of points (equal to steps) on the small
    circle described by the given latlon and radius (the latter being an
    angle as well).

    Math from github.com/vain/asciiworld.
    """
    # Get latitude of one point on the small circle. We can easily do
    # this by adjusting the latitude but we have to avoid pushing over a
    # pole.
    if lat > 0:
        slat = lat - degrees(r)
    else:
        slat = lat + degrees(r)

    # Geographic coordinates to spherical coordinates.
    s_theta, s_phi = latlon_to_spherical(lat, lon)

    # Cartesian coordinates of rotation axis.
    rx, ry, rz = spherical_to_cartesian(s_theta, s_phi)

    # Rotation matrix around r{x,y,z} by alpha.
    alpha = radians(360 / steps)

    M = []
    M.append(rx**2 * (1 - cos(alpha)) + cos(alpha))
    M.append(ry * rx * (1 - cos(alpha)) + rz * sin(alpha))
    M.append(rz * rx * (1 - cos(alpha)) - ry * sin(alpha))

    M.append(rx * ry * (1 - cos(alpha)) - rz * sin(alpha))
    M.append(ry**2 * (1 - cos(alpha)) + cos(alpha))
    M.append(rz * ry * (1 - cos(alpha)) + rx * sin(alpha))

    M.append(rx * rz * (1 - cos(alpha)) + ry * sin(alpha))
    M.append(ry * rz * (1 - cos(alpha)) - rx * sin(alpha))
    M.append(rz**2 * (1 - cos(alpha)) + cos(alpha))

    # Cartesian coordinates of initial vector.
    px, py, pz = latlon_to_cartesian(slat, lon)

    for i in range(steps):
        # Rotate p{x,y,z}.
        p2x = px * M[0] + py * M[3] + pz * M[6]
        p2y = px * M[1] + py * M[4] + pz * M[7]
        p2z = px * M[2] + py * M[5] + pz * M[8]

        # For acos(), force p2z back into [-1, 1] which *might* happen
        # due to precision errors.
        p2z_fixed = max(-1, min(1, p2z))

        # Use rotated p{x,y,z} as basis for next rotation.
        px = p2x
        py = p2y
        pz = p2z

        yield p2x, p2y, p2z_fixed


def draw_satellite(layer, body, satellite):
    try:
        x, y = body.from_latlon(satellite.latitude, satellite.longitude)
        layer.draw(x, y, "X", 16)
    except ValueError:
        pass


def draw_crosshair(layer, body, satellite):
    try:
        x, y = body.from_latlon(satellite.latitude, satellite.longitude)
    except ValueError:
        return
    for i in range(body.width-1):
        if body.map[i][y][3] is None:
            layer.draw(i, y, "─", 235)
    for i in range(body.height):
        if body.map[x][i][3] is None:
            layer.draw(x, i, "│", 235)


def draw_location(layer, body, lat, lon):
    if lat and lon:
        x, y = body.from_latlon(lat, lon)
        layer.draw(x, y, "•", 2)
