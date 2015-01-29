from copy import copy
from os.path import dirname, expanduser, join
import shelve

import shapefile

from .utils.geometry import point_in_poly


MAP_CACHE = "~/.termtrack_map_cache"


class Body(object):
    def __init__(self, width, height):
        self.height = height
        self.width = width
        self.lat_range = self.LAT_MAX - self.LAT_MIN
        self.lon_range = self.LON_MAX - self.LON_MIN
        self.pixel_percentage = 100 / (self.width * self.height)
        self._sf = shapefile.Reader(join(dirname(__file__), "data", self.SHAPEFILE))

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
        x = int(round((self.width - 1) * xrel))
        y = int(round((self.height - 1) * yrel))
        return min(x, self.width - 1), min(y, self.height - 1)

    def prepare_map(self):
        map_cache = shelve.open(expanduser(MAP_CACHE))
        try:
            map_cache_key = "{}_{}x{}".format(self.NAME, self.width, self.height)
            if map_cache_key in map_cache:
                self.map = map_cache[map_cache_key]
                raise StopIteration()
            progress = 0.0
            empty_line = [None for i in range(self.height)]
            self.map = [copy(empty_line) for i in range(self.width)]
            for x in range(self.width):
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
        xrel = x / (self.width - 1)
        yrel = y / (self.height - 1)
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
