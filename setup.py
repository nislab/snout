#! /usr/bin/python3
# -*- coding: utf-8 -*-

""" Installer for Snout

    This installer make sure all prerequisites are fulfilled and installs the application.

    Code inspirations:
    - https://gist.github.com/rochacbruno/90efe90e6549721e4189
"""

import pip

from setuptools import setup, find_packages

links = []
requires = [
    'appdirs',
    'logging_tree',
    'pywheel',
    'pyyaml',
    'click',
    'pyshark',
    'prettytable',
    'timeago',
]


def read_long_description():
    return ""


if __name__ == "__main__":
    setup(
        name='Snout',
        version="0.0.1",
        url='https://github.com/nislab/Snout',
        license='FREE',
        author="Johannes K Becker, John Mikulskis",
        author_email="{jkbecker,jkulskis}@bu.edu",
        maintainer="Johannes K Becker",
        maintainer_email="jkbecker@bu.edu",
        description='An SDR-Based Network Observation Utility Toolkit.',
        long_description=read_long_description(),
        packages=find_packages(),
        include_package_data=True,
        zip_safe=False,
        platforms='any',
        install_requires=requires,
        dependency_links=links,
        entry_points={
            "console_scripts": [
                "snout          = snout.cli:main",
                "snout-doctor   = snout.doctor:main",
            ]
        }
    )

    # If setup completed fine, set up an initial configuration
    from snout.core.config import Config as cfg
    import os
    pybombs_prefix = os.getenv('PYBOMBS_PREFIX', '/pybombs')
    cfg.reset(userprefix=pybombs_prefix, force=True)

    # If setup completed fine, move scapy-radio files to $HOME/.scapy-radio
    from pathlib import Path
    from glob import glob
    from shutil import copy

    print('Moving scapy-radio modulations to {}'.format(
        os.path.join(Path.home(), '.scapy-radio')))
    scapy_radio_dir = os.path.join(str(Path.home()), '.scapy-radio')
    scapy_radio_files = []
    for ext in ('*.py', '*.grc'):
        paths = [Path(p) for p in glob(os.path.join(
            'snout/modulations/**', ext), recursive=True)]
        scapy_radio_files.extend(paths)
    for src in scapy_radio_files:
        # don't include "snout/modulations" in the dst path
        dst = os.path.join(scapy_radio_dir, *src.parts[2:-1])
        # don't override existing modulation files
        if not os.path.exists(os.path.join(dst, src.parts[-1])):
            os.makedirs(dst, exist_ok=True)
            copy(src, dst)
    print('Finished moving scapy-radio modulations')
