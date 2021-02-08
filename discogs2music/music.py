# -*- coding: UTF-8 -*-
#
# copyright: 2020-2021, Frederico Martins
# author: Frederico Martins <http://github.com/fscm>
# license: SPDX-License-Identifier: MIT

"""Music app metadata handler.

This module handles the Music app metadata.

The following is a simple usage example::
  from .music import Music
  m = Music()
  #r = discogs.get_ratings()

The module contains the following public classes:
  - ITunes -- The main entry point. As the example above shows, the
    ITunes() class can be used to change metadata on the Music app.

All other classes in this module are considered implementation details.
"""

from functools import reduce
from progress.bar import Bar
from appscript import app


class Music:
  """Data handler.

  This class manages the Music app metadata.

  Args:
    logger (logger.Logger, optional): Logger to use.  Defaults to None.
  """

  CONVERTION_RATIO = 20

  def __init__(self, logger=None):
    self.__logger = logger
    self.__app = app('Music')
    self.__library = self.__app.library_playlists['Library']
    self.__tracks = self.__library.tracks()

  def set_ratings_from_discogs(self, ratings, songs=False, override=False):
    """Update the ratings from the Discogs ratings.

    Args:
        ratings (dict): Discogs ratings.
        songs (bool): Update songs rating instead of album rating.
          Defaults to False.
        override (bool): Override existing ratings. Defaults to False.
    """
    if self.__logger:
      self.__logger.info('Updating Music ratings.')
      if songs:
        self.__logger.info('Updating Songs instead of album ratings.')
    results = {
        'artists': {'miss': {}},
        'albums': {
            'miss': {},
            'updated': {},
            'not_updated': {}},
        'songs': {
            'miss': {},
            'updated': {},
            'not_updated': {}}}
    show_progress = True
    if self.__logger and self.__logger.level < self.__logger.Level.INFO:
      show_progress = False
    for track in Bar('Processing').iter(
            self.__tracks) if show_progress else self.__tracks:
      track_artist = track.artist().title()
      track_album = track.album().title()
      track_name = track.name().title()
      track_album_rating = int(track.album_rating())
      track_rating = int(track.rating())
      discogs_artist = ratings.get(track_artist, None)
      if discogs_artist is None:
        if self.__logger:
          self.__logger.debug(
              f'Artist "{track_artist}" not found on Discogs ratings.')
        results['artists']['miss'].setdefault(track_artist, 1)
        continue
      discogs_album = ratings[track_artist].get(track_album, None)
      if discogs_album is None:
        if self.__logger:
          self.__logger.debug(
              f'Album "{track_album}" not found on Discogs ratings.')
        results['albums']['miss'].setdefault(track_artist, {})
        results['albums']['miss'][track_artist].setdefault(track_album, 1)
        results['songs']['miss'].setdefault(track_artist, {})
        results['songs']['miss'][track_artist].setdefault(track_name, 0)
        results['songs']['miss'][track_artist][track_name] += 1
        continue
      discogs_rating = discogs_album['rating'] * self.CONVERTION_RATIO
      if songs:
        if track_rating == 0 or override:
          if self.__logger:
            self.__logger.debug(f'Updating song "{track_name}".')
          results['songs']['updated'].setdefault(track_artist, {})
          results['songs']['updated'][track_artist].setdefault(
              track_name, {'from': track_album_rating, 'to': discogs_rating})
          track.rating.set(discogs_rating)
        else:
          if self.__logger:
            self.__logger.debug(f'Song "{track_name}" not updated.')
          results['songs']['not_updated'].setdefault(track_artist, {})
          results['songs']['not_updated'][track_artist].setdefault(
              track_name, {'from': track_album_rating, 'to': discogs_rating})
      else:
        if track_album_rating == 0 or override:
          if self.__logger:
            self.__logger.debug(f'Updating album "{track_album}".')
          results['albums']['updated'].setdefault(track_artist, {})
          results['albums']['updated'][track_artist].setdefault(
              track_album, {'from': track_album_rating, 'to': discogs_rating})
          track.album_rating.set(discogs_rating)
        else:
          if self.__logger:
            self.__logger.debug(f'Album "{track_album}" not updated.')
          results['albums']['not_updated'].setdefault(track_artist, {})
          results['albums']['not_updated'][track_artist].setdefault(
              track_album, {'from': track_album_rating, 'to': discogs_rating})
    if self.__logger and self.__logger.level > self.__logger.Level.NONE:
      self.__logger.debug('Calculating stats.')
      artists_miss = reduce(
          lambda x, y: x + y,
          results['artists']['miss'].values() or [0])
      albums_miss = reduce(
          lambda x, y: x + y,
          map(
              lambda x: len(x.keys()),
              results['albums']['miss'].values() or [{}]) or [0])
      albums_updated = reduce(
          lambda x, y: x + y,
          map(
              lambda x: len(x.keys()),
              results['albums']['updated'].values() or [{}]) or [0])
      albums_not_updated = reduce(
          lambda x, y: x + y,
          map(
              lambda x: len(x.keys()),
              results['albums']['not_updated'].values() or [{}]) or [0])
      songs_miss = reduce(
          lambda x, y: x + y,
          map(
              lambda x: len(x.keys()),
              results['songs']['miss'].values() or [{}]) or [0])
      songs_updated = reduce(
          lambda x, y: x + y,
          map(
              lambda x: len(x.keys()),
              results['songs']['updated'].values() or [{}]) or [0])
      songs_not_updated = reduce(
          lambda x, y: x + y,
          map(
              lambda x: len(x.keys()),
              results['songs']['not_updated'].values() or [{}]) or [0])
      self.__logger.info(
          'Stats:\n'
          f'  {artists_miss} band misses\n'
          f'  {albums_miss} album misses\n'
          f'  {albums_updated} albums updated\n'
          f'  {albums_not_updated} albums not updated\n'
          f'  {songs_miss} song misses\n'
          f'  {songs_updated} songs updated\n'
          f'  {songs_not_updated} songs not updated\n')
