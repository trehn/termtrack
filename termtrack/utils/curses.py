import curses
from queue import Queue
from threading import Event, Lock
from time import sleep

from .geometry import point_distance


INPUT_CYCLE_ORBITS = 1
INPUT_EXIT = 2
INPUT_TIME_MINUS_LONG = 3
INPUT_TIME_MINUS_SHORT = 4
INPUT_TIME_PAUSE = 5
INPUT_TIME_PLUS_LONG = 6
INPUT_TIME_PLUS_SHORT = 7
INPUT_TIME_RESET = 8
INPUT_TOGGLE_COVERAGE = 9
INPUT_TOGGLE_CROSSHAIR = 10
INPUT_TOGGLE_FOOTPRINT = 11
INPUT_TOGGLE_GRID = 12
INPUT_TOGGLE_INFO = 13
INPUT_TOGGLE_NIGHT = 14
INPUT_TOGGLE_ORBIT_APSIDES = 15
INPUT_TOGGLE_ORBIT_ASCDESC = 16
INPUT_TOGGLE_TOPO = 17

KEYMAP = {
    "a": INPUT_TOGGLE_ORBIT_APSIDES,
    "c": INPUT_TOGGLE_COVERAGE,
    "d": INPUT_TOGGLE_ORBIT_ASCDESC,
    "f": INPUT_TOGGLE_FOOTPRINT,
    "g": INPUT_TOGGLE_GRID,
    "i": INPUT_TOGGLE_INFO,
    "KEY_DOWN": INPUT_TIME_MINUS_LONG,
    "KEY_LEFT": INPUT_TIME_MINUS_SHORT,
    "KEY_RIGHT": INPUT_TIME_PLUS_SHORT,
    "KEY_UP": INPUT_TIME_PLUS_LONG,
    "n": INPUT_TOGGLE_NIGHT,
    "o": INPUT_CYCLE_ORBITS,
    "p": INPUT_TIME_PAUSE,
    "q": INPUT_EXIT,
    "r": INPUT_TIME_RESET,
    "t": INPUT_TOGGLE_TOPO,
    "x": INPUT_TOGGLE_CROSSHAIR,
}

RGB_256 = (
    ((0, 0, 0), 1),
    ((229, 34, 0), 2),
    ((0, 194, 0), 3),
    ((199, 196, 0), 4),
    ((3, 67, 200), 5),
    ((201, 49, 199), 6),
    ((0, 197, 199), 7),
    ((199, 199, 199), 8),
    ((104, 104, 104), 9),
    ((255, 110, 103), 10),
    ((96, 250, 104), 11),
    ((255, 252, 102), 12),
    ((105, 113, 255), 13),
    ((255, 119, 255), 14),
    ((98, 253, 255), 15),
    ((255, 255, 255), 16),
    ((0, 0, 0), 17),
    ((2, 17, 115), 18),
    ((4, 26, 153), 19),
    ((6, 35, 189), 20),
    ((8, 43, 223), 21),
    ((11, 51, 255), 22),
    ((0, 111, 0), 23),
    ((0, 113, 114), 24),
    ((0, 115, 153), 25),
    ((0, 117, 189), 26),
    ((0, 119, 223), 27),
    ((0, 121, 255), 28),
    ((0, 149, 0), 29),
    ((0, 150, 114), 30),
    ((0, 151, 153), 31),
    ((0, 153, 189), 32),
    ((0, 154, 223), 33),
    ((0, 156, 255), 34),
    ((0, 184, 0), 35),
    ((0, 185, 114), 36),
    ((0, 186, 153), 37),
    ((0, 187, 189), 38),
    ((0, 188, 223), 39),
    ((0, 190, 255), 40),
    ((0, 217, 0), 41),
    ((0, 218, 114), 42),
    ((0, 219, 153), 43),
    ((0, 220, 189), 44),
    ((0, 221, 223), 45),
    ((0, 222, 255), 46),
    ((0, 249, 0), 47),
    ((0, 249, 114), 48),
    ((0, 250, 153), 49),
    ((0, 251, 189), 50),
    ((0, 252, 223), 51),
    ((0, 253, 255), 52),
    ((115, 12, 0), 53),
    ((116, 24, 114), 54),
    ((116, 31, 153), 55),
    ((116, 39, 189), 56),
    ((116, 46, 223), 57),
    ((116, 53, 255), 58),
    ((114, 112, 0), 59),
    ((114, 114, 114), 60),
    ((114, 116, 153), 61),
    ((115, 118, 189), 62),
    ((115, 120, 223), 63),
    ((115, 122, 255), 64),
    ((113, 150, 0), 65),
    ((113, 151, 114), 66),
    ((113, 152, 153), 67),
    ((114, 154, 189), 68),
    ((114, 155, 223), 69),
    ((114, 157, 255), 70),
    ((112, 185, 0), 71),
    ((112, 186, 114), 72),
    ((112, 187, 153), 73),
    ((112, 188, 189), 74),
    ((112, 189, 223), 75),
    ((113, 190, 255), 76),
    ((110, 218, 0), 77),
    ((110, 219, 114), 78),
    ((110, 219, 153), 79),
    ((110, 220, 189), 80),
    ((111, 221, 223), 81),
    ((111, 222, 255), 82),
    ((108, 249, 0), 83),
    ((108, 250, 114), 84),
    ((108, 250, 153), 85),
    ((108, 251, 189), 86),
    ((108, 252, 223), 87),
    ((109, 253, 255), 88),
    ((154, 20, 0), 89),
    ((154, 29, 114), 90),
    ((155, 35, 153), 91),
    ((155, 42, 189), 92),
    ((155, 49, 223), 93),
    ((155, 56, 255), 94),
    ((153, 114, 0), 95),
    ((154, 115, 114), 96),
    ((154, 117, 153), 97),
    ((154, 119, 189), 98),
    ((154, 121, 223), 99),
    ((154, 123, 255), 100),
    ((153, 151, 0), 101),
    ((153, 152, 114), 102),
    ((153, 153, 153), 103),
    ((153, 154, 189), 104),
    ((153, 156, 223), 105),
    ((153, 158, 255), 106),
    ((152, 185, 0), 107),
    ((152, 186, 114), 108),
    ((152, 187, 153), 109),
    ((152, 188, 189), 110),
    ((152, 189, 223), 111),
    ((152, 191, 255), 112),
    ((151, 218, 0), 113),
    ((151, 219, 114), 114),
    ((151, 220, 153), 115),
    ((151, 220, 189), 116),
    ((151, 223, 255), 117),
    ((151, 223, 255), 118),
    ((149, 250, 0), 119),
    ((149, 250, 114), 120),
    ((149, 251, 153), 121),
    ((150, 252, 189), 122),
    ((150, 252, 223), 123),
    ((150, 253, 255), 124),
    ((191, 27, 0), 125),
    ((191, 34, 114), 126),
    ((191, 40, 153), 127),
    ((191, 46, 189), 128),
    ((191, 52, 223), 129),
    ((191, 59, 255), 130),
    ((190, 115, 0), 131),
    ((190, 117, 114), 132),
    ((190, 118, 153), 133),
    ((190, 120, 189), 134),
    ((190, 122, 223), 135),
    ((190, 125, 255), 136),
    ((189, 152, 0), 137),
    ((189, 153, 114), 138),
    ((189, 154, 153), 139),
    ((190, 155, 189), 140),
    ((190, 157, 223), 141),
    ((190, 159, 255), 142),
    ((189, 186, 0), 143),
    ((189, 187, 114), 144),
    ((189, 188, 153), 145),
    ((189, 189, 189), 146),
    ((189, 190, 223), 147),
    ((189, 188, 255), 148),
    ((188, 219, 0), 149),
    ((188, 220, 114), 150),
    ((188, 220, 153), 151),
    ((188, 221, 189), 152),
    ((188, 222, 223), 153),
    ((188, 223, 255), 154),
    ((187, 250, 0), 155),
    ((187, 251, 113), 156),
    ((187, 251, 153), 157),
    ((187, 252, 189), 158),
    ((187, 253, 223), 159),
    ((187, 254, 255), 160),
    ((225, 34, 0), 161),
    ((225, 40, 114), 162),
    ((225, 45, 153), 163),
    ((225, 50, 189), 164),
    ((225, 56, 223), 165),
    ((225, 62, 255), 166),
    ((224, 116, 0), 167),
    ((224, 118, 114), 168),
    ((224, 119, 153), 169),
    ((224, 121, 189), 170),
    ((224, 123, 223), 171),
    ((225, 126, 255), 172),
    ((224, 153, 0), 173),
    ((224, 154, 114), 174),
    ((224, 155, 153), 175),
    ((224, 156, 189), 176),
    ((224, 158, 223), 177),
    ((224, 160, 255), 178),
    ((223, 187, 0), 179),
    ((223, 188, 113), 180),
    ((223, 189, 153), 181),
    ((223, 190, 189), 182),
    ((223, 191, 223), 183),
    ((224, 192, 255), 184),
    ((222, 219, 0), 185),
    ((222, 220, 113), 186),
    ((223, 221, 153), 187),
    ((223, 222, 189), 188),
    ((223, 223, 223), 189),
    ((223, 224, 255), 190),
    ((222, 251, 0), 191),
    ((222, 251, 113), 192),
    ((222, 252, 152), 193),
    ((222, 253, 189), 194),
    ((222, 253, 223), 195),
    ((222, 254, 255), 196),
    ((255, 40, 0), 197),
    ((255, 46, 113), 198),
    ((255, 50, 153), 199),
    ((255, 55, 189), 200),
    ((255, 60, 223), 201),
    ((255, 66, 255), 202),
    ((255, 118, 0), 203),
    ((255, 120, 113), 204),
    ((255, 121, 153), 205),
    ((255, 123, 189), 206),
    ((255, 125, 223), 207),
    ((255, 127, 255), 208),
    ((255, 154, 0), 209),
    ((255, 155, 113), 210),
    ((255, 156, 152), 211),
    ((255, 157, 189), 212),
    ((255, 159, 223), 213),
    ((255, 161, 255), 214),
    ((255, 188, 0), 215),
    ((255, 189, 113), 216),
    ((255, 190, 152), 217),
    ((255, 191, 189), 218),
    ((255, 192, 223), 219),
    ((255, 193, 255), 220),
    ((255, 220, 0), 221),
    ((255, 221, 113), 222),
    ((255, 222, 152), 223),
    ((255, 222, 189), 224),
    ((255, 223, 223), 225),
    ((255, 225, 255), 226),
    ((255, 251, 0), 227),
    ((255, 252, 113), 228),
    ((255, 252, 152), 229),
    ((255, 253, 188), 230),
    ((255, 254, 223), 231),
    ((255, 255, 255), 232),
    ((23, 23, 23), 234),
    ((37, 37, 37), 235),
    ((51, 51, 51), 236),
    ((63, 63, 63), 237),
    ((75, 75, 75), 238),
    ((86, 86, 86), 239),
    ((97, 97, 97), 240),
    ((107, 107, 107), 241),
    ((117, 117, 117), 242),
    ((127, 127, 127), 243),
    ((137, 137, 137), 244),
    ((146, 146, 146), 245),
    ((156, 156, 156), 246),
    ((165, 165, 165), 247),
    ((174, 174, 174), 248),
    ((183, 183, 183), 249),
    ((191, 191, 191), 250),
    ((200, 200, 200), 251),
    ((209, 209, 209), 252),
    ((217, 217, 217), 253),
    ((225, 225, 225), 254),
)
RGB_CACHE = {}


def bresenham(points, width, height, connect_ends=False):
    """
    Takes a sequential(!) list of points within a wrapping canvas of the
    given dimensions and yields a new series of points including the
    original points with filler points added in between to create
    continous lines.
    """
    if connect_ends:
        previous_point = points[-1]
    else:
        previous_point = None
    connected_points = []

    for point in points:
        connected_points.append(point)
        if previous_point is None:
            previous_point = point
            continue
        # since we have a wrapping canvas, there are three straight
        # paths between every two points: one inside the canvas and two
        # going off to each side
        # our first task is to find out which one is the shortest
        candidate_points = (
            (point[0], point[1]),  # inside canvas
            (point[0] + width, point[1]),  # through right edge
            (point[0] - width, point[1]),  # through left edge
        )
        smallest_distance = float("inf")
        closest_point = None
        for candidate_point in candidate_points:
            distance = point_distance(previous_point, candidate_point)
            if distance < smallest_distance:
                closest_point = candidate_point
                smallest_distance = distance

        # now that we know the direction we have to go, we can start the
        # actual Bresenham magic

        p1x, p1y = previous_point
        p2x, p2y = closest_point

        delta_x = abs(p2x - p1x)
        delta_y = abs(p2y - p1y)

        steep = delta_y > delta_x
        if steep:
            p1x, p1y = p1y, p1x
            p2x, p2y = p2y, p2x
        if p1x > p2x:
            p1x, p2x = p2x, p1x
            p1y, p2y = p2y, p1y

        delta_x = p2x - p1x
        delta_y = abs(p2y - p1y)

        error = delta_x // 2

        step_y = 1 if p1y < p2y else -1
        y = p1y

        for x in range(p1x, p2x + 1):
            if steep:
                connected_points.append((y, x))
            else:
                connected_points.append((x, y))
            error -= delta_y
            if error < 0:
                y += step_y
                error += delta_x

        previous_point = point

    for point in connected_points:
        yield point_wrap(point[0], point[1], width, height)


def closest_color(r, g, b):
    if (r, g, b) in RGB_CACHE.keys():
        return RGB_CACHE[(r, g, b)]
    best_candidate = 0
    best_distance = 765
    for rgb, candidate in RGB_256:
        distance = abs(r - rgb[0]) + abs(g - rgb[1]) + abs(b - rgb[2])
        if distance < best_distance:
            best_candidate = candidate
            best_distance = distance
    RGB_CACHE[(r, g, b)] = best_candidate
    return best_candidate


def fill_outline(center, outline_points, width, height):
    queue = [center]
    while queue:
        current_pixel = queue.pop()
        if current_pixel not in outline_points:
            outline_points.add(current_pixel)
            for next_pixel in get_adjacent(current_pixel[0], current_pixel[1], width, height):
                queue.append(next_pixel)


def get_adjacent(x, y, width, height):
    """
    Returns a list of tuples with coordinates adjacent to x, y.
    """
    adjacent_unwrapped = (
        (x-1, y),
        (x+1, y),
        (x, y+1),
        (x, y-1),
    )
    adjacent_wrapped = []
    for u_x, u_y in adjacent_unwrapped:
        if u_y < 0 or u_y >= height:
            continue
        adjacent_wrapped.append(point_wrap(u_x, u_y, width, height))
    return tuple(adjacent_wrapped)


def graceful_ctrlc(func):
    """
    Makes the decorated function terminate silently on CTRL+C.
    """
    def wrapper(*args, **kwargs):
        try:
            func(*args, **kwargs)
        except KeyboardInterrupt:
            pass
    return wrapper


def input_thread_body(stdscr, input_queue, quit_event, curses_lock):
    while not quit_event.is_set():
        try:
            with curses_lock:
                key = stdscr.getkey()
        except:
            key = None
        try:
            input_queue.put(KEYMAP[key])
        except KeyError:
            # key not bound
            pass
        sleep(0.01)


def point_wrap(x, y, width, height):
    return (x + width) % width, (y + height) % height


def setup(stdscr):
    # curses
    curses.use_default_colors()
    curses.start_color()
    curses.use_default_colors()
    for i in range(0, curses.COLORS):
        curses.init_pair(i + 1, i, -1)
    curses.curs_set(False)
    stdscr.timeout(0)

    # prepare input thread mechanisms
    curses_lock = Lock()
    input_queue = Queue()
    quit_event = Event()
    return (curses_lock, input_queue, quit_event)
