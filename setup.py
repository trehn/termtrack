from setuptools import find_packages, setup

setup(
    name="termtrack",
    version="0.7.3",
    description="Track Earth-orbiting satellites from your terminal",
    author="Torsten Rehn",
    author_email="torsten@rehn.email",
    license="GPLv3",
    url="https://github.com/trehn/termtrack",
    keywords=["terminal", "track", "tracking", "satellite", "orbit", "iss"],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Console :: Curses",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Natural Language :: English",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: POSIX",
        "Operating System :: Unix",
        "Programming Language :: Python :: 3",
        "Topic :: Utilities",
    ],
    packages=find_packages(),
    package_data={
        "termtrack": [
            "data/earth.jpg",
            "data/mars.jpg",
            "data/moon.jpg",
            "data/ne_110m_land.dbf",
            "data/ne_110m_land.shp",
            "data/ne_110m_land.shx",
        ],
    },
    install_requires=[
        "click >= 2.0",
        "Pillow >= 2.7.0",
        "pyephem >= 3.7.5.0",
        "pyshp >= 1.2.1",
        "requests >= 2.0.0",
    ],
    entry_points={
        'console_scripts': [
            "termtrack=termtrack.cli:main",
        ],
    },
)
