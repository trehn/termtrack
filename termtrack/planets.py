from os.path import dirname, join

from skyfield.api import load
from skyfield.jpllib import SpiceKernel


TIMESCALE = load.timescale()
EPHEMERIS = SpiceKernel(join(dirname(__file__), "data", "de421.bsp"))

# Planets with moons use barycenter in the ephemeris
PLANETS = {
    'earth': EPHEMERIS['earth'],
    'jupiter': EPHEMERIS['jupiter barycenter'],
    'mars': EPHEMERIS['mars barycenter'],
    'mercury': EPHEMERIS['mercury'],
    'moon': EPHEMERIS['moon'],
    'neptune': EPHEMERIS['neptune barycenter'],
    'pluto': EPHEMERIS['pluto barycenter'],
    'saturn': EPHEMERIS['saturn barycenter'],
    'sun': EPHEMERIS['sun'],
    'uranus': EPHEMERIS['uranus barycenter'],
    'venus': EPHEMERIS['venus'],
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


def latlon_for_planet(planet_name, time):
    time = TIMESCALE.from_datetime(time)
    astrometric = PLANETS['earth'].at(time).observe(PLANETS[planet_name])
    apparent = astrometric.apparent()
    ra, dec, _ = apparent.radec()
    gmst_degrees = time.gmst * 15.0

    longitude = ra.degrees - gmst_degrees
    while longitude > 180:
        longitude -= 360
    while longitude < -180:
        longitude += 360

    return dec.degrees, longitude
