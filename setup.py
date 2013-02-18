#!/usr/bin/env python

from distutils.core import setup

import vingd

setup(
    name=vingd.__name__,
    version=vingd.__version__,
    description=vingd.__doc__,
    long_description=open('README.rst').read(),
    author=vingd.__author__,
    author_email=vingd.__author_email__,
    url=vingd.__url__,
    packages=[vingd.__name__],
    package_dir={vingd.__name__: vingd.__name__},
    license=vingd.__license__,
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Programming Language :: Python',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Topic :: Internet',
        'Topic :: Office/Business :: Financial',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ]
)
