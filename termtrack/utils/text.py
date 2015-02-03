def format_seconds(seconds, hide_seconds=False):
    """
    Returns a human-readable string representation of the given amount
    of seconds.
    """
    if seconds < 1:
        return "0s"
    output = ""
    for period, period_seconds in (
        ('y', 31557600),
        ('d', 86400),
        ('h', 3600),
        ('m', 60),
        ('s', 1),
    ):
        if seconds >= period_seconds and not (hide_seconds and period == 's'):
            output += str(int(seconds / period_seconds))
            output += period
            output += " "
            seconds = seconds % period_seconds
    return output.strip()
