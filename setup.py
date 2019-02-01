from __future__ import print_function
from setuptools import setup
from setuptools.command.test import test as TestCommand

setup(
    name='chargestop',
    version='0.0.1',
    url='http://github.com/alexblanck/chargestop',
    license='Apache Software License',
    author='Alex Blanck',
    install_requires=['requests', 'configargparse'],
    setup_requires=['pytest-runner'],
    tests_require=['pytest', 'responses'],
    author_email='alex@alexblanck.com',
    description='Save money by stopping ChargePoint sessions if it appears that your car is done charging',
    packages=['chargestop']
)
