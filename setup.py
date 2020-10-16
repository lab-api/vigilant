from distutils.core import setup
from setuptools import find_packages

setup(
    name='vigilant',
    version='0.1',
    description='Reactive monitoring framework',
    author='Robert Fasano',
    author_email='robert.j.fasano@colorado.edu',
    packages=find_packages(exclude=['docs']),
    license='MIT',
    # entry_points={
    # "console_scripts": [
    #     "vigilant-daemon = vigilant.tick.daemon",
    # ]
    # }
)
