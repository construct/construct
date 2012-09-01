#!/usr/bin/env python
import os
from setuptools import find_packages, setup

HERE = os.path.dirname(__file__)
exec(open(os.path.join(HERE, "construct", "version.py")).read())

setup(
    name = "construct",
    version = version_string, #@UndefinedVariable
    packages = find_packages(),
    license = "MIT",
    description = "A powerful declarative parser for binary data",
    long_description = open("README.rst").read(),
    platforms = ["POSIX", "Windows"],
    url = "https://github.com/construct/construct",
    author = "Tomer Filiba, Corbin Simpson",
    author_email = "tomerfiliba@gmail.com, MostAwesomeDude@gmail.com",
    install_requires = ["six"],
    classifiers = [
        "Development Status :: 5 - Production/Stable",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 2.5",
        "Programming Language :: Python :: 2.6",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.0",
        "Programming Language :: Python :: 3.1",
        "Programming Language :: Python :: 3.2",
    ],
    test_suite = "tests",
)
