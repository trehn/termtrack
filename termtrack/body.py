from copy import copy
from os.path import dirname, expanduser, join
import shelve

from PIL import Image
import shapefile

from .utils.curses import closest_color
from .utils.geometry import latlon_to_spherical, point_in_poly, spherical_to_cartesian


MAP_CACHE = "~/.termtrack_map_cache"


class Body(object):
    def __init__(self, width, height):
        self.height = height
        self.width = width
        self.pixel_percentage = 100 / (self.width * self.height)
        self._img = Image.open(join(dirname(__file__), "data", self.COLORMAP))
        if self.SHAPEFILE is not None:
            self._sf = shapefile.Reader(join(dirname(__file__), "data", self.SHAPEFILE))

    def from_latlon(self, lat, lon):
        xrel = (lon + 180) / 360
        yrel = (-lat + 90) / 180
        x = round((self.width - 1) * xrel)
        y = round((self.height - 1) * yrel)
        return min(x, self.width - 1), min(y, self.height - 1)

    def prepare_map(self):
        map_cache = shelve.open(expanduser(MAP_CACHE))
        try:
            map_cache_key = "{}_{}x{}".format(self.NAME, self.width, self.height)
            if map_cache_key in map_cache:
                self.map = map_cache[map_cache_key]
                return
            progress = 0.0
            empty_line = [None for i in range(self.height)]
            self.map = [copy(empty_line) for i in range(self.width)]

            img = self._img.resize((self.width, self.height))
            pixels = img.load()

            for x in range(self.width):
                for y in range(self.height):
                    yield progress
                    color = r = g = b = None
                    lat, lon = self._to_latlon(x, y)
                    if self.SHAPEFILE is not None:
                        for shape in self._sf.iterShapes():
                            if (
                                # for performance reasons we quickly check the
                                # bounding box before trying the more expensive
                                # point_in_poly() call
                                lat > shape.bbox[1] and
                                lat < shape.bbox[3] and
                                lon > shape.bbox[0] and
                                lon < shape.bbox[2]
                            ) and point_in_poly(lon, lat, shape.points):
                                r, g, b = pixels[x, y]
                                color = closest_color(r, g, b)
                                break
                    else:
                        r, g, b = pixels[x, y]
                        color = closest_color(r, g, b)
                    spherical = latlon_to_spherical(lat, lon)
                    cartesian = spherical_to_cartesian(*spherical)
                    self.map[x][y] = (r, g, b, color, (lat, lon), spherical, cartesian)
                    progress += self.pixel_percentage
                    yield progress
            map_cache[map_cache_key] = self.map
        finally:
            map_cache.close()

    def to_cartesian(self, x, y):
        return self.map[x][y][6]

    def to_latlon(self, x, y):
        return self.map[x][y][4]

    def _to_latlon(self, x, y):
        xrel = x / (self.width - 1)
        yrel = y / (self.height - 1)
        return (
            90 - yrel * 180,
            xrel * 360 - 180,
        )

    def to_spherical(self, x, y):
        return self.map[x][y][5]


class Earth(Body):
    NAME = "Earth"
    COLORMAP = "earth.jpg"
    SHAPEFILE = "ne_110m_land.shp"


class Mars(Body):
    NAME = "Mars"
    COLORMAP = "mars.jpg"
    SHAPEFILE = None


class Moon(Body):
    NAME = "Moon"
    COLORMAP = "moon.jpg"
    SHAPEFILE = None


BODY_MAP = {
    'earth': Earth,
    'luna': Moon,
    'mars': Mars,
    'moon': Moon,
    'terra': Earth,
}
