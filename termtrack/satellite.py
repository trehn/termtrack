from datetime import datetime, timedelta
from math import asin, atan2, cos, degrees, pi, radians, sin, sqrt

from requests import get
from skyfield.api import EarthSatellite as SkyfieldSatellite, wgs84

from . import VERSION_STRING
from .planets import TIMESCALE


ALIASES = {
    'hst': 20580,
    'hubble': 20580,
    'iss': 25544,
    'landsat7': 25682,
    'landsat8': 39084,
    'qzs-1': 37158,
    'qzs1': 37158,
    'smap': 40376,
}
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


class EarthSatellite:
    def __init__(
        self,
        number,
        time,
        observer_latitude=0,
        observer_longitude=0,
        observer_elevation=0,
        tle_file=None,
    ):
        if tle_file is not None:
            with open(tle_file) as f:
                tle = f.read().strip().split("\n")
        elif number is not None:
            number = ALIASES.get(number, number)
            response = get(
                f"https://celestrak.org/NORAD/elements/gp.php?CATNR={number}&FORMAT=TLE",
                headers={"User-Agent": f"termtrack/{VERSION_STRING}"},
            )
            if response.status_code == 403:
                raise ValueError(
                    "CelesTrak returned 403 (probably rate limit). "
                    "Try again later or use --tle"
                )
            response.raise_for_status()
            tle = response.text.strip().split("\n")
            if tle == ["No TLE found"]:
                raise ValueError(f"Unable to find TLE for {number}")
        else:
            raise ValueError("No SATCAT number or TLE file provided")

        if len(tle) < 3:
            raise ValueError(f"Invalid TLE format: expected 3 lines, got {len(tle)}")
        self.name = tle[0].strip()
        self._satellite = SkyfieldSatellite(tle[1], tle[2], self.name, TIMESCALE)

        model = self._satellite.model
        if model.no_kozai == 0:
            raise ValueError("Invalid TLE: mean motion is zero")

        self.argument_of_periapsis = model.argpo
        self.eccentricity = model.ecco
        self.inclination = model.inclo
        self.mean_anomaly_at_epoch = model.mo
        self.right_ascension_of_ascending_node = model.nodeo

        # mean motion: model.no_kozai is in radians per minute,
        # convert to revolutions per day for orbital period
        self.mean_motion_revs_per_day = model.no_kozai * 1440 / (2 * pi)
        self.orbital_period = timedelta(days=1) / self.mean_motion_revs_per_day
        self.mean_motion = 2 * pi / self.orbital_period.total_seconds()

        self.epoch = self._satellite.epoch.utc_datetime()

        self.apoapsis_latitude = degrees(asin(
            sin(self.argument_of_periapsis + pi) * sin(self.inclination)
        ))
        self.periapsis_latitude = degrees(asin(
            sin(self.argument_of_periapsis) * sin(self.inclination)
        ))
        self.semi_major_axis = semi_major_axis(self.mean_motion)
        self.apoapsis_altitude = self.semi_major_axis * (1 + self.eccentricity) - \
                                 earth_radius_at_latitude(self.apoapsis_latitude)
        self.periapsis_altitude = self.semi_major_axis * (1 - self.eccentricity) - \
                                  earth_radius_at_latitude(self.periapsis_latitude)

        self.observer_elevation = observer_elevation
        self.observer_latitude = observer_latitude
        self.observer_longitude = observer_longitude

        self.compute(time)

    def compute(self, time, plus_seconds=0):
        target_time = time + timedelta(seconds=plus_seconds)
        time = TIMESCALE.from_datetime(target_time)

        geocentric = self._satellite.at(time)
        position = wgs84.geographic_position_of(geocentric)

        self.altitude = position.elevation.m
        self.latitude = position.latitude.degrees
        self.longitude = position.longitude.degrees

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
        self.time_to_periapsis = timedelta(seconds=self.orbital_period.total_seconds() -
                                                   self.time_since_periapsis.total_seconds())
        self.time_since_apoapsis = timedelta(seconds=(self.mean_anomaly + pi) % (2 * pi) /
                                                     self.mean_motion)
        self.time_to_apoapsis = timedelta(seconds=self.orbital_period.total_seconds() -
                                                  self.time_since_apoapsis.total_seconds())
        self.velocity = orbital_velocity(self.semi_major_axis, self.altitude, self.latitude)

        periapsis_time = TIMESCALE.from_datetime(target_time + self.time_to_periapsis)
        geocentric_periapsis = self._satellite.at(periapsis_time)
        position_periapsis = wgs84.geographic_position_of(geocentric_periapsis)
        self.periapsis_latitude = position_periapsis.latitude.degrees
        self.periapsis_longitude = position_periapsis.longitude.degrees

        apoapsis_time = TIMESCALE.from_datetime(target_time + self.time_to_apoapsis)
        geocentric_apoapsis = self._satellite.at(apoapsis_time)
        position_apoapsis = wgs84.geographic_position_of(geocentric_apoapsis)
        self.apoapsis_latitude = position_apoapsis.latitude.degrees
        self.apoapsis_longitude = position_apoapsis.longitude.degrees

        if (
            self.observer_latitude is not None and
            self.observer_longitude is not None
        ):
            observer = wgs84.latlon(
                self.observer_latitude,
                self.observer_longitude,
                elevation_m=self.observer_elevation,
            )
            difference = self._satellite - observer
            topocentric = difference.at(time)
            alt, az, _ = topocentric.altaz()

            self.observer_azimuth = az.radians
            self.observer_altitude = alt.radians

            self.acquisition_of_signal = None
            self.loss_of_signal = None

            one_day_ahead = TIMESCALE.utc(
                target_time.year, target_time.month, target_time.day,
                target_time.hour + 24, target_time.minute, target_time.second,
            )

            for event_time, event_type in zip(*self._satellite.find_events(
                observer,
                time,
                one_day_ahead,
                altitude_degrees=0.0,
            )):
                if event_type == 0 and self.acquisition_of_signal is None:  # rise
                    self.acquisition_of_signal = event_time.utc_datetime()
                elif event_type == 2 and self.loss_of_signal is None:  # set
                    self.loss_of_signal = event_time.utc_datetime()
