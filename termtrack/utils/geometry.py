from math import acos, atan2, cos, degrees, radians, sin, sqrt


def cartesian_to_latlon(x, y, z):
    return spherical_to_latlon(*cartesian_to_spherical(x, y, z))


def cartesian_to_spherical(x, y, z):
    return acos(z), atan2(y, x)


def latlon_to_cartesian(lat, lon):
    return spherical_to_cartesian(*latlon_to_spherical(lat, lon))


def latlon_to_spherical(lat, lon):
    return -radians(lat) + radians(90), radians(lon)


def point_distance(point1, point2):
    return sqrt(abs((point2[0] - point1[0]) ** 2 - (point2[1] - point1[1]) ** 2))


def point_in_poly(x, y, poly):
    n = len(poly)
    inside = False
    p1x, p1y = poly[0]
    for i in range(n+1):
        p2x, p2y = poly[i % n]
        if y > min(p1y, p2y):
            if y <= max(p1y, p2y):
                if x <= max(p1x, p2x):
                    if p1y != p2y:
                        xints = (y-p1y) * (p2x-p1x) / (p2y-p1y) + p1x
                    if p1x == p2x or x <= xints:
                        inside = not inside
        p1x, p1y = p2x, p2y
    return inside


def spherical_to_cartesian(theta, phi):
    x = sin(theta) * cos(phi)
    y = sin(theta) * sin(phi)
    z = cos(theta)
    return x, y, z


def spherical_to_latlon(theta, phi):
    return degrees(radians(90) - theta), degrees(phi)
