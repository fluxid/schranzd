#!/usr/bin/env python

from distutils.core import setup

setup(
    name = 'schranzd',
    description = 'Schranz Daemon',
    author = 'Tomasz Kowalczyk', 
    packages = (
        'schranz',
        'schranz.modules',
    ),
    package_dir = {
        'schranz': 'src/schranz',
        'schranz.modules': 'src/schranz/modules',
    },
    data_files = (
        ('/etc/init.d', ('rc/ubuntu/schranzd',)),
        ('/var/lib/schranz', ('utils/merge_config.sh',)),
    ),
    scripts = (
        'src/sch',
        'src/schranzd',
    ),
)
