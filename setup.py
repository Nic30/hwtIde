#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

from setuptools import setup, find_packages

setup(name='hwtIde',
      version='0.1',
      description='IDE for HWToolkit (fpga devel. tools)',
      url='https://github.com/Nic30/hwtIde',
      author='Michal Orsak',
      author_email='michal.o.socials@gmail.com',
      install_requires=[
          'hwt',  # core library of HWToolkit
          'jinja2',  # templates renderer
          'flask'  # webserver of visualizer
          'pyDigitalWaveTools', # vcd parsing and manipulation
      ],
      license='MIT',
      packages=find_packages(),
      package_data={'hwtIde': ['*.html', '*.js', '*.css', '*.ico',
                               '*.png', '*.oft', '*.eot', '*.svg',
                               '*.ttf', '*.woff']},
      include_package_data=True,
      zip_safe=False)
