from setuptools import find_packages
from setuptools import setup
import os


def read_file(name):
    with open(os.path.join(os.path.dirname(__file__), name)) as f:
        return f.read()


version = '1.0b4'
shortdesc = "Deliver web resources"
longdesc = '\n\n'.join([read_file(name) for name in [
    'README.rst',
    os.path.join('docs', 'source', 'overview.rst'),
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
    ],
    keywords='web resources dependencies javascript CSS',
    author='Cone Contributors',
    author_email='dev@conestack.org',
    url='http://github.com/conestack/webresource',
    license='Simplified BSD',
    packages=['webresource'],
    zip_safe=True,
    install_requires=['setuptools'],
    extras_require=dict(
        test=['coverage'],
        docs=['Sphinx']
    )
)
