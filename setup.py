from distutils.core import setup
from setuptools import find_packages

setup(
    name='watchdog',
    version='0.1',
    description='Reactive monitoring framework for experimental physics',
    author='Robert Fasano',
    author_email='robert.j.fasano@colorado.edu',
    packages=find_packages(exclude=['docs']),
    license='MIT',
    long_description=open('README.md').read(),
    install_requires=['plotly', 'IPython', 'jupyter']
)
