from datetime import datetime, timedelta
import re

import ephem
from requests import get

from .utils.geometry import rad_to_deg


TLE_REGEX = re.compile("PRE>(.*)</PRE", flags=re.DOTALL)


class EarthSatellite(object):
    def __init__(self, number):
        raw_html = get("http://www.celestrak.com/cgi-bin/TLE.pl?CATNR={}".format(number)).text
        tle = TLE_REGEX.search(raw_html).group(1).strip().split("\n")
        self._satellite = ephem.readtle(*tle)

    def latlon(self, plus_minutes=0):
        self._satellite.compute(datetime.utcnow() + timedelta(minutes=plus_minutes))
        return rad_to_deg(self._satellite.sublat), rad_to_deg(self._satellite.sublong)
