from math import degrees

import ephem


PLANETS = {
    'jupiter': ephem.Jupiter(),
    'mars': ephem.Mars(),
    'mercury': ephem.Mercury(),
    'moon': ephem.Moon(),
    'neptune': ephem.Neptune(),
    'pluto': ephem.Pluto(),
    'saturn': ephem.Saturn(),
    'sun': ephem.Sun(),
    'uranus': ephem.Uranus(),
    'venus': ephem.Venus(),
}

PLANET_SYMBOLS = {
    'jupiter': "♃",
    'mars': "♂",
    'mercury': "☿",
    'moon': "☽",
    'neptune': "♆",
    'pluto': "♇",
    'saturn': "♄",
    'sun': "☼",
    'uranus': "⛢",
    'venus': "♀",
}


def latlon_for_planet(planet_name, date):
    planet = PLANETS[planet_name]
    obs = ephem.Observer()
    obs.date = date
    obs.lat = 0
    obs.lon = 0
    planet.compute(date)
    return degrees(planet.dec), degrees(ephem.degrees(planet.ra - obs.sidereal_time()).znorm)
