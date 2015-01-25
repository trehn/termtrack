#!/usr/bin/env python3

import curses
from queue import Empty, Queue
from threading import Event, Lock, Thread
from time import sleep

import click


INPUT_EXIT = 1


def setup(stdscr):
    # curses
    curses.use_default_colors()
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


def print_version(ctx, param, value):
    if not value or ctx.resilient_parsing:
        return
    click.echo(VERSION)
    ctx.exit()


@graceful_ctrlc
def render(
        stdscr,
        fps=1,
        **kwargs
    ):
    curses_lock, input_queue, quit_event = setup(stdscr)
    input_thread = Thread(
        args=(stdscr, input_queue, quit_event, curses_lock),
        target=input_thread_body,
    )
    input_thread.start()
    try:
        while True:
            with curses_lock:
                stdscr.erase()
                stdscr.addstr(0, 0, "hi", curses.color_pair(1))
            try:
                input_action = input_queue.get(True, 1/fps)
            except Empty:
                input_action = None
            if input_action == INPUT_EXIT:
                break
    finally:
        quit_event.set()
        input_thread.join()


@click.command()
@click.option("-f", "--fps", default=1, metavar="N",
              help="Frames per second (defaults to 1)")
@click.option("--version", is_flag=True, callback=print_version,
              expose_value=False, is_eager=True,
              help="Show version and exit")
def main(**kwargs):
    curses.wrapper(render, **kwargs)


if __name__ == '__main__':
    main()
