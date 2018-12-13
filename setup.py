#!/usr/bin/env python

from setuptools import setup

setup(
    name='takt',
    version='0.0.1',
    description='sampler that can be controlled using ableton push',
    author='Jannis Uhlendorf',
    packages=['takt'],
    dependency_links=['https://github.com/belangeo/pyo'],
    entry_points={
        'console_scripts': [
            'takt = takt.ui:main'
        ]
    }
)
