#!/usr/bin/env python

import os

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

HERE = os.path.dirname(__file__)
exec(open(os.path.join(HERE, "construct", "version.py")).read())

setup(
    name = "construct",
    version = version_string, #@UndefinedVariable
    packages = [
        'construct',
        'construct.lib', 
        'construct.examples', 
        'construct.examples.formats', 
        'construct.examples.formats.data', 
        'construct.examples.formats.executable', 
        'construct.examples.formats.filesystem', 
        'construct.examples.formats.graphics',
        'construct.examples.protocols', 
    ],
    license = "MIT",
    description = "A powerful declarative parser/builder for binary data",
    long_description = open(os.path.join(HERE, "README.rst")).read(),
    platforms = ["POSIX", "Windows"],
    url = "http://construct.readthedocs.org",
    author = "Arkadiusz Bulski, Tomer Filiba, Corbin Simpson",
    author_email = "arek.bulski@gmail.com, tomerfiliba@gmail.com, MostAwesomeDude@gmail.com",
    install_requires = [],
    requires = [],
    provides = ["construct"],
    keywords = "construct, declarative, data structure, binary, parser, builder, pack, unpack",
    classifiers = [
        "Development Status :: 5 - Production/Stable",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.3",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: Implementation :: PyPy",
    ],
)
