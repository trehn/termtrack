from copy import copy
from os.path import dirname, expanduser, join
import shelve

from PIL import Image
import shapefile

from .utils.curses import closest_color
from .utils.geometry import point_in_poly


MAP_CACHE = "~/.termtrack_map_cache"


class Body(object):
    LON_MIN = -180
    LON_CROPPED_MIN = LON_MIN
    LON_MAX = 180
    LON_CROPPED_MAX = LON_MAX
    LAT_MIN = -90
    LAT_CROPPED_MIN = LAT_MIN
    LAT_MAX = 90
    LAT_CROPPED_MAX = LAT_MAX

    def __init__(self, width, height):
        self.height = height
        self.width = width
        self.lat_range = self.LAT_CROPPED_MAX - self.LAT_CROPPED_MIN
        self.lon_range = self.LON_CROPPED_MAX - self.LON_CROPPED_MIN
        self.pixel_percentage = 100 / (self.width * self.height)
        self._img = Image.open(join(dirname(__file__), "data", self.COLORMAP))
        if self.SHAPEFILE is not None:
            self._sf = shapefile.Reader(join(dirname(__file__), "data", self.SHAPEFILE))

    def from_latlon(self, lat, lon):
        if (
            lat > self.LAT_CROPPED_MAX or
            lat < self.LAT_CROPPED_MIN or
            lon > self.LON_CROPPED_MAX or
            lon < self.LON_CROPPED_MIN
        ):
            raise ValueError()
        xrel = (lon - self.LON_CROPPED_MIN) / self.lon_range
        yrel = (self.LAT_CROPPED_MAX - lat) / self.lat_range
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

            crop_left = int((self._img.size[0] / 2) * (1 - (self.LON_CROPPED_MIN / self.LON_MIN)))
            crop_right = int((self._img.size[0] / 2) + (self._img.size[0] / 2) * (self.LON_CROPPED_MAX / self.LON_MAX))
            crop_top = int((self._img.size[1] / 2) * (1 - (self.LAT_CROPPED_MAX / self.LAT_MAX)))
            crop_bottom = int((self._img.size[1] / 2) + (self._img.size[1] / 2) * (self.LAT_CROPPED_MIN / self.LAT_MIN))
            img = self._img.crop((crop_left, crop_top, crop_right, crop_bottom))
            img = img.resize((self.width, self.height))
            pixels = img.load()

            for x in range(self.width):
                for y in range(self.height):
                    yield progress
                    color = r = g = b = None
                    if self.SHAPEFILE is not None:
                        lat, lon = self.to_latlon(x, y)
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
                    self.map[x][y] = (r, g, b, color)
                    progress += self.pixel_percentage
                    yield progress
            map_cache[map_cache_key] = self.map
        finally:
            map_cache.close()

    def to_latlon(self, x, y):
        xrel = x / (self.width - 1)
        yrel = y / (self.height - 1)
        return (
            self.LAT_CROPPED_MAX - yrel * self.lat_range,
            self.LON_CROPPED_MIN + xrel * self.lon_range,
        )


class Earth(Body):
    LAT_CROPPED_MIN = -60
    LAT_CROPPED_MAX = 85
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
