#!/usr/bin/env python

from distutils.core import setup

setup(name='etekcity_scale',
      version='0.1',
      description='Etekcity scale interface library',
      author='Paul Banks',
      url='https://paulbanks.org/projects/etekcity',
      packages=['etekcity_scale'],
      install_requires=[
          'bleak',
      ],
)
