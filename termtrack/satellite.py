from datetime import datetime, timedelta
from math import asin, atan2, cos, degrees, pi, radians, sin, sqrt
import re

import ephem
from requests import get


ALIASES = {
    'iss': 25544,
    'tiangong': 37820,
}
TLE_REGEX = re.compile("PRE>(.*)</PRE", flags=re.DOTALL)
EARTH_FLATTENING_COEFFICIENT = 0.003352891869237217
EARTH_RADIUS = 6378135
EARTH_SGP = 3.986004418e+14  # Standard gravitational parameter
KEPLER_ACCURACY = 1e-6


def earth_radius_at_latitude(latitude):
    latitude = radians(abs(latitude))
    return EARTH_RADIUS * sqrt(
        1 -
        (2 * EARTH_FLATTENING_COEFFICIENT -
            (EARTH_FLATTENING_COEFFICIENT ** 2)
        )
        * (sin(latitude) ** 2)
    )


def epoch(yy, days):
    if int(yy) > 56:
        year = int("19" + yy)
    else:
        year = int("20" + yy)
    return datetime(year, 1, 1) + timedelta(days=float(days)-1)


def keplers_equation(mean_anomaly, eccentricity):
    eccentric_anomaly = mean_anomaly
    while True:
        d = eccentric_anomaly - eccentricity * sin(eccentric_anomaly) - mean_anomaly
        eccentric_anomaly -= d / (1 - eccentricity * cos(eccentric_anomaly))
        if abs(d) < KEPLER_ACCURACY:
            break
    return eccentric_anomaly


def semi_major_axis(mean_motion):
    return (EARTH_SGP / (mean_motion ** 2)) ** (1/3)


def orbital_velocity(semi_major_axis, altitude, latitude):
    return sqrt(
        EARTH_SGP * (
            (2 / (earth_radius_at_latitude(latitude) + altitude)) - (1 / semi_major_axis)
        )
    )


class EarthSatellite(object):
    def __init__(self, number, observer_latitude=0, observer_longitude=0, observer_elevation=0):
        number = ALIASES.get(number, number)
        raw_html = get("http://www.celestrak.com/cgi-bin/TLE.pl?CATNR={}".format(number)).text
        tle = TLE_REGEX.search(raw_html).group(1).strip().split("\n")
        self._satellite = ephem.readtle(*tle)
        self.argument_of_periapsis = float(self._satellite._ap.norm)
        self.eccentricity = self._satellite._e
        self.epoch = self._satellite._epoch.datetime()
        self.inclination = float(self._satellite._inc.norm)
        self.mean_anomaly_at_epoch = float(self._satellite._M.norm)
        self.mean_motion_revs_per_day = self._satellite._n
        self.name = tle[0].strip()
        self.observer_elevation = observer_elevation
        self.observer_latitude = observer_latitude
        self.observer_longitude = observer_longitude
        self.orbital_period = timedelta(days=1) / self.mean_motion_revs_per_day
        self.mean_motion = 2 * pi / self.orbital_period.total_seconds()
        self.apoapsis_latitude = degrees(asin(
            sin(self.argument_of_periapsis + pi) * sin(self.inclination)
        ))
        self.periapsis_latitude = degrees(asin(
            sin(self.argument_of_periapsis) * sin(self.inclination)
        ))
        self.right_ascension_of_ascending_node = float(self._satellite._raan.norm)
        self.semi_major_axis = semi_major_axis(self.mean_motion)
        self.apoapsis_altitude = self.semi_major_axis * (1 + self.eccentricity) - earth_radius_at_latitude(self.apoapsis_latitude)
        self.periapsis_altitude = self.semi_major_axis * (1 - self.eccentricity) - earth_radius_at_latitude(self.periapsis_latitude)
        self.compute()

    def compute(self, plus_seconds=0):
        target_time = datetime.utcnow() + timedelta(seconds=plus_seconds)
        self._satellite.compute(target_time)
        self.altitude = self._satellite.elevation
        self.latitude = degrees(self._satellite.sublat)
        self.longitude = degrees(self._satellite.sublong)
        self.mean_anomaly = (
            self.mean_anomaly_at_epoch +
            self.mean_motion * (
                (target_time - self.epoch).total_seconds() %
                self.orbital_period.total_seconds()
            )
        ) % (2 * pi)
        self.eccentric_anomaly = keplers_equation(self.mean_anomaly, self.eccentricity)
        self.true_anomaly = 2 * atan2(
            sqrt(1 + self.eccentricity) * sin(self.eccentric_anomaly / 2),
            sqrt(1 - self.eccentricity) * cos(self.eccentric_anomaly / 2)
        )
        self.time_since_periapsis = timedelta(seconds=self.mean_anomaly / self.mean_motion)
        self.time_to_periapsis = timedelta(seconds=self.orbital_period.total_seconds() - self.time_since_periapsis.total_seconds())
        self.time_since_apoapsis = timedelta(seconds=(self.mean_anomaly + pi) % (2 * pi) / self.mean_motion)
        self.time_to_apoapsis = timedelta(seconds=self.orbital_period.total_seconds() - self.time_since_apoapsis.total_seconds())
        self.velocity = orbital_velocity(self.semi_major_axis, self.altitude, self.latitude)

        self._satellite.compute(target_time + self.time_to_periapsis)
        self.periapsis_latitude = degrees(self._satellite.sublat)
        self.periapsis_longitude = degrees(self._satellite.sublong)

        self._satellite.compute(target_time + self.time_to_apoapsis)
        self.apoapsis_latitude = degrees(self._satellite.sublat)
        self.apoapsis_longitude = degrees(self._satellite.sublong)

        if self.observer_latitude is not None and self.observer_longitude is not None and plus_seconds == 0:
            observer = ephem.Observer()
            observer.elevation = self.observer_elevation
            observer.lat = str(self.observer_latitude)
            observer.lon = str(self.observer_longitude)
            self._satellite.compute()
            self._satellite.compute(observer)
            self.observer_azimuth = float(self._satellite.az.norm)
            self.observer_altitude = float(self._satellite.alt.znorm)
