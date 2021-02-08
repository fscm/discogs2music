#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
#
# copyright: 2020-2021, Frederico Martins
# author: Frederico Martins <http://github.com/fscm>
# license: SPDX-License-Identifier: MIT

"""Setup discogs2music."""

from setuptools import setup
from discogs2music import (
    __author__, __author_email__, __license__, __project__, __version__)

if __name__ == '__main__':
  setup(
      author=__author__,
      author_email=__author_email__,
      classifiers=[
          'Development Status :: 4 - Beta',
          'Environment :: Console',
          'Intended Audience :: End Users/Desktop',
          'License :: OSI Approved :: MIT License',
          'Operating System :: MacOS :: MacOS X',
          'Programming Language :: Python :: 3.6',
          'Topic :: Utilities',
          'Typing :: Typed'],
      description=(
          'Update your Music app media ratings with your Discogs ratings'),
      # include_package_data=True,
      install_requires=[
          'appscript>=1.1.2',
          'progress>=1.5',
          'requests>=2.25.1'],
      license=__license__,
      long_description=open('README.md', 'r', encoding='utf-8').read(),
      long_description_content_type='text/markdown',
      name=__project__,
      packages=[__project__],
      package_data={'': ['LICENSE'], __project__: ['py.typed', '*.pyi']},
      platforms=['Mac OS-X'],
      python_requires='~=3.6',
      url='https://github.com/fscm/discogs2music',
      version=__version__,
      scripts=['bin/' + __project__])
