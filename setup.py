#!/usr/bin/env python

from distutils.core import setup

setup(
    name = 'schranzd',
    description = 'Schranz Daemon',
    author = 'Tomasz Kowalczyk', 
    packages = (
        'schranz',
    ),
    package_dir = {
        'schranz': 'src/schranz'
    },
    data_files = (
        ('/etc/init.d', ('rc/ubuntu/schranzd',)),
    ),
    scripts = (
        'src/sch',
        'src/schranzd',
    ),
)
