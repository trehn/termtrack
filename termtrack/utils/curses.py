import curses
from queue import Queue
from threading import Event, Lock
from time import sleep


INPUT_EXIT = 1


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
        if key in ("q", "Q"):
            input_queue.put(INPUT_EXIT)
        sleep(0.01)
