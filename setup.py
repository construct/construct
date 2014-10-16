#!/usr/bin/env python
import os
try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

HERE = os.path.dirname(__file__)
exec(open(os.path.join(HERE, "construct", "version.py")).read())

setup(
    name="construct",
    version=version_string,  #@UndefinedVariable
    packages=[
        'construct',
        'construct.lib',
        'construct.formats',
        'construct.formats.data',
        'construct.formats.executable',
        'construct.formats.filesystem',
        'construct.formats.graphics',
        'construct.protocols',
        'construct.protocols.application',
        'construct.protocols.layer2',
        'construct.protocols.layer3',
        'construct.protocols.layer4',
    ],
    license="MIT",
    description="A powerful declarative parser/builder for binary data",
    long_description=open(os.path.join(HERE, "README.rst")).read(),
    platforms=["POSIX", "Windows"],
    url="http://construct.readthedocs.org",
    author="Tomer Filiba, Corbin Simpson",
    author_email="tomerfiliba@gmail.com, MostAwesomeDude@gmail.com",
    install_requires=["six"],
    requires=["six"],
    provides=["construct"],
    keywords="construct, declarative, data structure, "
        "binary, parser, builder, pack, unpack",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 2.5",
        "Programming Language :: Python :: 2.6",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.0",
        "Programming Language :: Python :: 3.1",
        "Programming Language :: Python :: 3.2",
        "Programming Language :: Python :: 3.3",
    ],
)
