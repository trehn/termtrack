from datetime import datetime, timedelta


def pixel_from_layers(x, y, layers):
    for layer in layers:
        if layer.hidden:
            continue
        try:
            return layer.content[(x, y)]
        except KeyError:
            pass
    return " ", 1


class Layer(object):
    def __init__(self, update_callback, update_timeout=0):
        self.content = {}
        self.hidden = False
        self.last_updated = None
        self.update_callback = update_callback
        if update_timeout is None:
            self.update_timeout = None
        else:
            self.update_timeout = timedelta(seconds=update_timeout)

    def draw(self, x, y, char, color):
        self.content[(x, y)] = (char, color)

    def update(self, *args, **kwargs):
        if (
            self.hidden or
            (self.last_updated and (
                self.update_timeout is None or
                datetime.now() - self.last_updated < self.update_timeout
            ))
        ):
            return

        self.last_updated = datetime.now()
        self.content = {}
        self.update_callback(self, *args, **kwargs)
