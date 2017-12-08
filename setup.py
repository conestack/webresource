# -*- coding: utf-8 -*-
from setuptools import find_packages
from setuptools import setup
import os


def read_file(name):
    with open(os.path.join(os.path.dirname(__file__), name)) as f:
        return f.read()


version = '0.1.dev0'
shortdesc = "Manage web resources and dependencies"
longdesc = '\n\n'.join([read_file(name) for name in [
    'README.rst',
    'CHANGES.rst',
    'LICENSE.rst'
]])


setup(
    name='webresource',
    version=version,
    description=shortdesc,
    long_description=longdesc,
    classifiers=[
        'License :: OSI Approved :: BSD License',
        'Intended Audience :: Developers',
        'Topic :: Software Development',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ],
    keywords='web resource dependencies javascript CSS',
    author='Robert Niederreiter',
    author_email='office@squarewave.at',
    url='http://github.com/rnixx/webresource',
    license='BSD',
    packages=['webresource'],
    zip_safe=True,
    install_requires=[
        'setuptools'
    ],
    extras_require={
    },
    test_suite='webresource.test_suite',
    entry_points="""
    """
)
