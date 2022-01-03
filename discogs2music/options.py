# -*- coding: UTF-8 -*-
#
# copyright: 2020-2022, Frederico Martins
# author: Frederico Martins <http://github.com/fscm>
# license: SPDX-License-Identifier: MIT

"""Command-line parsing module.

This module is based on the argparse command-line parsing library.

The following is a simple usage example::
  from .options import Options
  o = Options()
  for opt in o.options:
      print(opt, o.options[opt], type(o.options[opt]))

The module contains the following public classes:
  - Options -- The main entry point for command-line parsing. As the
    example above shows, the Options() class is used to parse the
    arguments.

All other classes in this module are considered implementation details.
"""

import argparse
from os import getcwd
from . import __version__


class Options:
  """Command-line options parser.

  This class uses the argparse.ArgumentParser to parse and validate
  the command-line options.
  """

  __default_file = f'{getcwd()}/discogs2music.json'

  def __init__(self):
    parser = argparse.ArgumentParser(
        prog=__package__,
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        add_help=True,
        allow_abbrev=False)
    mutually_exclusive = parser.add_mutually_exclusive_group(required=False)
    parser.add_argument(
        '-a',
        '--apikey',
        action='store',
        nargs=1,
        type=str,
        required=True,
        help='discogs api key')
    parser.add_argument(
        '-d',
        '--datafile',
        action='store',
        nargs=1,
        default=self.__default_file,
        type=str,
        help='path to the datafile')
    mutually_exclusive.add_argument(
        '--debug',
        action='store_true',
        help='debug mode')
    parser.add_argument(
        '-l',
        '--local',
        action='store_true',
        help='use local file only (does not query discogs for data)')
    parser.add_argument(
        '-o',
        '--override',
        action='store_true',
        help='override local data')
    mutually_exclusive.add_argument(
        '-q',
        '--quiet',
        action='store_true',
        help='quiet mode')
    parser.add_argument(
        '-s',
        '--songs',
        action='store_true',
        help='update songs rating instead of album rating')
    parser.add_argument(
        '-v',
        '--version',
        action='version',
        version=__version__)
    self.__options = parser.parse_args()

  @property
  def apikey(self):
    """str: apikey option."""
    return self.__options.apikey[0]

  @property
  def datafile(self):
    """str: data file option."""
    return self.__options.datafile

  @property
  def debug(self):
    """bool: debug option."""
    return self.__options.debug

  @property
  def local(self):
    """bool: local option."""
    return self.__options.local

  @property
  def options(self):
    """dict: all options."""
    return {
        key: (
            value[0] if isinstance(
                value,
                list) else value) for (
            key,
            value) in vars(
            self.__options).items()}

  @property
  def override(self):
    """bool: override local data option."""
    return self.__options.override

  @property
  def quiet(self):
    """bool: quiet option."""
    return self.__options.quiet

  @property
  def songs(self):
    """bool: update songs instead option."""
    return self.__options.songs
