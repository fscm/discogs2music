# -*- coding: UTF-8 -*-
#
# copyright: 2020-2022, Frederico Martins
# author: Frederico Martins <http://github.com/fscm>
# license: SPDX-License-Identifier: MIT

"""Discogs data handler.

This module handles Discogs data.

The following is a simple usage example::
  from .discogs import Discogs
  d = Discogs('my_discogs_secret_token')
  r = discogs.get_ratings()
  print(r)

The module contains the following public classes:
  - Discogs -- The main entry point. As the example above shows, the
    Discogs() class can be used to load data from Discogs.

All other classes in this module are considered implementation details.
"""

import json
import re
from time import time, sleep
from progress.bar import Bar
from requests import sessions


class Discogs:
  """Data handler.

  This class loads data from Discogs.

  Args:
    key (str): Discogs API key.
    logger (logger.Logger, optional): Logger to use. Defaults to None.
  """

  API_BASEURL = 'https://api.discogs.com'
  API_FORMAT = 'application/vnd.discogs.v2.plaintext+json'
  API_LIMIT = 100
  API_RATELIMIT_STATUS = 429
  API_RATELIMIT_TIME = 61

  def __init__(self, key, logger=None):
    self.__api_last_block_time = time()
    self.__headers = {
        'Accept': f'{self.API_FORMAT}',
        'Accept-Encoding': 'gzip',
        'Content-Type': 'application/json',
        'User-Agent': f'{__package__}'}
    self.__key = key
    self.__logger = logger
    self.__params = {
        'token': f'{self.__key}',
        'per_page': self.API_LIMIT}
    self.__session = sessions.Session()
    self.__identity = self.__request(f'{self.API_BASEURL}/oauth/identity')

  def __request(self, url, params=None):
    """Private method to perform a request to the Discogs API.

    Args:
      url (str): Request URL.
      params (dict[str, Any], optional): Extra requests params.
        Defaults to None.

    Returns:
      dict[str, Any]: Discogs API data.
    """
    response = self.__session.get(
        url,
        params={**self.__params, **params} if params else self.__params,
        headers=self.__headers)
    headers = response.headers
    status_code = response.status_code
    remaining_queries = int(headers.get('X-Discogs-Ratelimit-Remaining', 60))
    if (remaining_queries < 2) or (status_code == self.API_RATELIMIT_STATUS):
      if self.__logger:
        self.__logger.warning('API rate limit reacehd.')
      now = time()
      sleep(max(
          2,
          self.API_RATELIMIT_TIME - (now - self.__api_last_block_time)))
      self.__api_last_block_time = now
      return self.__request(url=url, params=params)
    return json.loads(response.content)

  def get_ratings(self, ratings=None):
    """Fetch Discogs ratings from the user's collection.

    Args:
      ratings (dict[str, Any], optional): Ratings. If provided this
        ratings will be updated. Defaults to None.

    Returns:
      dict[str, Any]: Ratings.
    """
    if self.__logger:
      self.__logger.info('Fetching ratings from Discogs.')
    last_updated = int(time())
    collection_info = self.__request(
        url=f'{self.__identity["resource_url"]}/collection/folders/0',
        params={'page': 1})
    total_albums = int(collection_info.get('count', 0))
    total_pages = -(-total_albums // self.API_LIMIT)
    if ratings:
      ratings = ratings.get('ratings', {})
    else:
      ratings = {}
    show_progress = True
    if self.__logger and self.__logger.level < self.__logger.Level.INFO:
      show_progress = False
    for step in Bar('Processing').iter(
            range(total_pages)) if show_progress else range(total_pages):
      page = step + 1
      if self.__logger:
        self.__logger.debug(f'Fetching page {page}')
      content = self.__request(
          f'{self.__identity["resource_url"]}/collection/folders/0/releases',
          params={'page': page})
      releases = content['releases']
      for release in releases:
        release_album_rating = int(release['rating'])
        release_album = release['basic_information']['title'].title()
        release_artist = ' - '.join(map(
            lambda x: re.sub(r'\(\d+\)', '', x['name']).strip(),
            release['basic_information']['artists'])).title()
        if self.__logger:
          self.__logger.debug(
              f'{release_artist} - [{release_album_rating}] {release_album} ')
        ratings.setdefault(release_artist, {})
        ratings[release_artist].setdefault(release_album, {})
        ratings[release_artist][release_album].setdefault(
            'rating',
            release_album_rating)
    return {'last_updated': last_updated, 'ratings': ratings}
