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
	  your convenience, the aliases listed below are also allowed).

	  Satellite aliases:
	      hubble          Hubble Space Telescope
	      iss             International Space Station
	      tiangong        Tiangong-1 (Chinese space station)

	  Hotkeys:
	      a       Toggle apsides markers
	      c       Toggle crosshair
	      d       Toggle ascent/descent markers
	      f       Toggle footprint (satellite horizon)
	      g       Toggle latitude/longitude grid
	      i       Toggle info panels
	      o       Cycle through drawing 0-3 next orbits
	      q       Quit

	Options:
	  --apsides                 Draw apoapsis and periapsis markers
	  -b, --body BODY           Which celestial body to draw: Earth, Moon or Mars
	                            (defaults to Earth)
	  -c, --crosshair           Draw crosshair around satellite location
	  -f, --footprint           Draw satellite footprint/horizon
	  --fps N                   Frames per second (defaults to 1)
	  -g, --grid                Draw latitude/longitude grid
	  -N, --no-night            Don't shade night side
	  -o, --orbits N            Draw this many orbits ahead of the satellite
	  --orbit-ascdesc           Draw orbits with ascent/descent markers
	  -O, --observer 'LAT LON'  Space-separated latitude and longitude of an
	                            observer; overrides IP-geolocation
	  -r, --orbit-res [/]N      Set distance of orbit markers: 'N' means N
	                            minutes, '/N' means 1/Nth of orbital period
	                            (defaults to /70)
	  -T, --no-topo             Disable rendering of topographical features
	  -Y, --no-you              Don't auto-detect your location as observer
	  --version                 Show version and exit
	  --help                    Show this message and exit

Credit goes to `vain/asciiworld <https://github.com/vain/asciiworld>`_ for inspiration and some tasty pieces of code.

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

------------------------------------------------------------------------

Known Issues
============

When looking at the ISS, you may notice some inconsistencies:

* the apoapsis/periapsis altitudes from the info panel do not match up with live altitude values when the satellite actually is at that point
* sometimes the current altitude is lower/higher than periapsis/apoapsis altitude
* the location of apoapsis/periapsis markers from --apsides are not located at the transition points between plus and minus signs drawn by --orbit-ascdesc

Where do these errors come from? The locations of the apsides are derived from the true anomaly which matches values from http://www.satellite-calculations.com/TLETracker/SatTracker.htm so I'm assuming that's not the source of the error. The shape of the Earth also does not explain the deviations in altitude.

Interestingly enough, when you look at more eccentric orbits like that of QZS-1 (37158) the errors seem to disappear, suggesting that the issue is merely inaccuracy instead of a plain wrong calculation somewhere.
