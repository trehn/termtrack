from datetime import datetime, timedelta
import re

import ephem
from requests import get

from .utils.geometry import rad_to_deg


ALIASES = {
    'iss': 25544,
    'tiangong': 37820,
}
TLE_REGEX = re.compile("PRE>(.*)</PRE", flags=re.DOTALL)


class EarthSatellite(object):
    def __init__(self, number):
        number = ALIASES.get(number, number)
        raw_html = get("http://www.celestrak.com/cgi-bin/TLE.pl?CATNR={}".format(number)).text
        tle = TLE_REGEX.search(raw_html).group(1).strip().split("\n")
        self.name = tle[0].strip()
        self.orbital_period = timedelta(days=1) / float(tle[2][52:63])
        self._satellite = ephem.readtle(*tle)

    def latlon(self, plus_seconds=0):
        self._satellite.compute(datetime.utcnow() + timedelta(seconds=plus_seconds))
        return rad_to_deg(self._satellite.sublat), rad_to_deg(self._satellite.sublong)
