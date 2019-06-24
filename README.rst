TermTrack
---------

Track orbiting objects (such as the International Space Station) in your terminal!

.. image:: https://raw.githubusercontent.com/trehn/termtrack/master/screenshot.png
    :alt: Screenshot

Requires Python 3.3+ and a terminal with 256 colors. A black background is highly recommended.

.. code-block::

	pip3 install termtrack
	termtrack -figmntxo 1 iss

.. code-block::

	Usage: termtrack [OPTIONS] [SATELLITE]

	  Shows a world map tracking SATELLITE. Valid values for SATELLITE are
	  numbers from http://www.celestrak.com/NORAD/elements/master.php (for
	  your convenience, a number of aliases have been provided).

	  Example satellite aliases (find more with --aliases):
	      hubble          Hubble Space Telescope
	      iss             International Space Station

	  Hotkeys:
	      a       Toggle apsides markers
	      c       Toggle next-orbit coverage overlay
	      d       Toggle ascent/descent markers
	      f       Toggle footprint (satellite horizon)
	      g       Toggle latitude/longitude grid
	      i       Toggle info panels
	      n       Toggle night shading
	      o       Cycle through drawing 0-3 next orbits
	      p       Pause/resume
	      q       Quit
	      r       Reset plotted time to current
	      t       Toggle topography
	      x       Toggle crosshair
	      left    Small step back in time
	      right   Small step forward in time
	      down    Large step back in time
	      up      Large step forward in time

	Options:
	  --aliases                 Show all satellite aliases and exit
	  --apsides                 Draw apoapsis and periapsis markers
	  -b, --body BODY           Which celestial body to draw: Earth, Moon or Mars
	                            (defaults to Earth)
	  -c, --coverage            Show next-orbit coverage overlay
	  -f, --footprint           Draw satellite footprint/horizon
	  --fps N                   Frames per second (defaults to 1)
	  -g, --grid                Draw latitude/longitude grid
	  -i, --info                Show info panels
	  -m, --me                  Auto-detect your location as observer
	  -n, --night               Shade night side
	  -o, --orbits N            Draw this many orbits ahead of the satellite
	  --orbit-ascdesc           Draw orbits with ascent/descent markers
	  -O, --observer 'LAT LON'  Space-separated latitude and longitude of an
	                            observer; overrides IP-geolocation
	  -p, --paused              Start paused
	  -P, --planets PLANETS     Comma-separated list of celestial objects to draw
	                            (e.g. 'sun,moon')
	  -r, --orbit-res [/]N[+]   Set distance of orbit markers: 'N' means N
	                            minutes, '/N' means 1/Nth of orbital period,
	                            append a plus sign to interpolate in between
	                            markers (defaults to /70)
	  -t, --topo                Enable coloring of topographical features
	  --tle FILE                read TLE data from FILE instead of downloading it
	                            (SATELLITE will have no effect and can be omitted)
	  -x, --crosshair           Draw crosshair around satellite location
	  --version                 Show version and exit
	  --help                    Show this message and exit

Credit goes to `vain/asciiworld <https://github.com/vain/asciiworld>`_ for inspiration and some tasty pieces of code.

------------------------------------------------------------------------

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

How Stuff Works
===============

To draw the map, TermTrack will look at a shapefile from `Natural Earth <http://www.naturalearthdata.com>`_ in order to find coordinates that are within a landmass. While computationally expensive, this method yields the most accurate and good-looking maps at all terminal sizes. To determine the color of each pixel, a relatively low-resolution and low-quality JPEG image is used. If you look at the image (``termtrack/data/earth.jpg``), you'll notice it has green oceans. This is to ensure that ocean blue will not spill over into coastal areas during downsampling. Same goes for the expanded white coast of Antarctica. Finally, the image has been tuned to produce good-looking colors against a black background. The resolution and quality of the image is not really a concern since we do not need maximum per-pixel precision to make the Sahara appear yellow. After computing land/ocean status and land color, this information is cached in ``~/.termtrack_map_cache``, so it will not have to be rendered again for the current terminal size.

For Mars and the Moon there is no shapefile to read and the entire area is colored according to similar JPEG color maps.

Night shading for each pixel is done by looking at the Sun's elevation (as computed by `pyephem <http://rhodesmill.org/pyephem/>`_) and shifting the color of the pixel towards blue accordingly. Twilight starts when the Sun is 18° below the horizon (`astronomical twilight <https://en.wikipedia.org/wiki/Twilight#Astronomical_twilight>`_) and ends when it has risen to 0°.

Satellite locations are derived from `TLE <https://en.wikipedia.org/wiki/Two-line_element_set>`_ data downloaded from `CelesTrak <https://celestrak.com/>`_. The data is fed into pyephem where the current position of the satellite is computed using `SGP4 <https://en.wikipedia.org/wiki/Simplified_perturbations_models>`_. Most of the data you see in the info panels is provided by pyephem, but the apsides' locations as well as the satellite footprint outline are computed by TermTrack itself.


Known Issues
============

When looking at the ISS, you may notice some inconsistencies:

* the apoapsis/periapsis altitudes from the info panel do not match up with live altitude values when the satellite actually is at that point
* sometimes the current altitude is lower/higher than periapsis/apoapsis altitude
* the location of apoapsis/periapsis markers from ``--apsides`` are not located at the transition points between plus and minus signs drawn by ``--orbit-ascdesc``

Where do these errors come from? The locations of the apsides are derived from the true anomaly which matches values from http://www.satellite-calculations.com/TLETracker/SatTracker.htm so I'm assuming that's not the source of the error. The shape of the Earth also does not explain the deviations in altitude.

Interestingly enough, when you look at more eccentric orbits like that of QZS-1 (37158) the errors seem to disappear, suggesting that the issue is merely inaccuracy instead of a plain wrong calculation somewhere.
