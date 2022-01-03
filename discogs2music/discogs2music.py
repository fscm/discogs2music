# -*- coding: UTF-8 -*-
#
# copyright: 2020-2022, Frederico Martins
# author: Frederico Martins <http://github.com/fscm>
# license: SPDX-License-Identifier: MIT

"""Discogs2Music

This module updated the Music app ratings using your Discogs ratings.

The following is a simple usage example::
  d2m = Discogs2Music()
  d2m.main()

The module contains the following public classes:
  - Discogs2Music -- The main entry point. As the example above shows,
    the Discogs2Music() class can be used to start the application that
    will update the Music app ratings.

All other classes in this module are considered implementation details.
"""

from . import __author__, __license__, __version__
from .data import Data
from .discogs import Discogs
from .music import Music
from .options import Options
from .logger import Logger


class Discogs2Music:
  """Update your Music app albums or songs rating with your Discogs
  ratings.
  """

  __header: str = (
      f'Discogs to Music version {__version__}\n'
      f'by {__author__} under {__license__} license')

  def main(self) -> None:
    """main method"""
    options = Options()
    logger = Logger(**({'level': Logger.Level.NONE} if options.quiet else {}),
                    **({'level': Logger.Level.DEBUG} if options.debug else {}))
    if not options.quiet:
      print(self.__header)
    data = Data(file=options.datafile, logger=logger)
    ratings = data.load()
    new_ratings = ratings
    if not options.local:
      discogs = Discogs(key=options.apikey, logger=logger)
      new_ratings = discogs.get_ratings(ratings=ratings)
    data.save(new_ratings)
    music = Music(logger=logger)
    music.set_ratings_from_discogs(
        ratings=new_ratings['ratings'],
        songs=options.songs,
        override=options.override)

def main() -> None:
  d2m = Discogs2Music()
  d2m.main()
