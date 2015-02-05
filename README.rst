TermTrack
---------

Track orbiting objects (such as the International Space Station) in your terminal!

.. image:: https://raw.githubusercontent.com/trehn/termtrack/master/screenshot.png
    :alt: Screenshot

Requires a terminal with 256 colors. A black background is highly recommended.

.. code-block::

	pip install termtrack

.. code-block::

	Usage: termtrack [OPTIONS] [SATELLITE]

	  Shows a world map tracking SATELLITE. Valid values for SATELLITE are
	  numbers from http://www.celestrak.com/NORAD/elements/master.asp (for
	  your convenience, "iss" or "tiangong" are also allowed).

	  Hotkeys:
	      i       Toggle info panels
	      q       Quit

	Options:
	  --apsides                 Draw apoapsis and periapsis markers
	  -b, --body BODY           Which celestial body to draw: Earth, Moon or Mars
	                            (defaults to Earth)
	  -c, --crosshair           Draw crosshair around satellite location
	  -f, --fps N               Frames per second (defaults to 1)
	  -N, --no-night            Don't shade night side
	  -o, --orbits N            Draw this many orbits ahead of the satellite
	  -O, --observer 'LAT LON'  Space-separated latitude and longitude of an
	                            observer; overrides IP-geolocation
	  -r, --orbit-res [/]N      Set distance of orbit markers: 'N' means N
	                            minutes, '/N' means 1/Nth of orbital period
	                            (defaults to /70)
	  -T, --no-topo             Disable rendering of topographical features
	  -Y, --no-you              Don't auto-detect your location as observer
	  --version                 Show version and exit
	  --help                    Show this message and exit

Credit goes to `vain/asciiworld <https://github.com/vain/asciiworld>`_ for inspiration.

------------------------------------------------------------------------

.. image:: http://img.shields.io/pypi/dm/termtrack.svg
    :target: https://pypi.python.org/pypi/termtrack/
    :alt: Downloads per month

.. image:: http://img.shields.io/pypi/v/termtrack.svg
    :target: https://pypi.python.org/pypi/termtrack/
    :alt: Latest Version

.. image:: http://img.shields.io/badge/Python-3.3+-green.svg
    :target: https://pypi.python.org/pypi/termtrack/
    :alt: Python 3.3+

.. image:: http://img.shields.io/badge/License-GPLv3-red.svg
    :target: https://pypi.python.org/pypi/termtrack/
    :alt: License
