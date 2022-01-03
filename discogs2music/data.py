# -*- coding: UTF-8 -*-
#
# copyright: 2020-2022, Frederico Martins
# author: Frederico Martins <http://github.com/fscm>
# license: SPDX-License-Identifier: MIT

"""Data parsing module.

This module loads and saves json data from and to a data file.

The following is a simple usage example::
  from .data import Data
  d = Data('my_file.json')
  json_data = d.load()
  d.save(json_data)

The module contains the following public classes:
  - Data -- The main entry point. As the example above shows, the
    Data() class can be used to load and save json data from a file.

All other classes in this module are considered implementation details.
"""

import json
from os import path


class Data:
  """Data parser.

  This class loads and saves json data from and to a data file.

  Args:
    file (str, optional): Data file. Defaults to None.
    logger (logger.Logger, optional): Logger to use.  Defaults to None.
  """

  def __init__(self, file=None, logger=None):
    self.__file = file
    self.__logger = logger

  def load(self):
    """Loads json data from a data file.

    Returns:
      dict: The json data.
    """
    if self.__logger:
      self.__logger.info(f'Loading data from "{self.__file}"')
    data = None
    if path.isfile(self.__file):
      in_file = open(self.__file, 'r')
      try:
        data = json.load(in_file)
      except ValueError as err:
        if self.__logger:
          self.__logger.error(f'Error loading data from "{self.__file}"')
          self.__logger.debug(str(err))
      in_file.close()
    else:
      if self.__logger:
        self.__logger.warning(f'Data file not found ({self.__file})')
    return data

  def save(self, data):
    """Saves json data to a data file.

    Args:
      data (dict): data to save.
    """
    if self.__logger:
      self.__logger.info(f'Writing data to "{self.__file}"')
    out_file = open(self.__file, 'w')
    try:
      json.dump(
          data,
          out_file,
          check_circular=True,
          ensure_ascii=False,
          skipkeys=True)
    except BaseException as err:
      if self.__logger:
        self.__logger.error(f'Unable to write to "{self.__file}"')
        self.__logger.error(str(err))
        self.__logger.debug(str(err))
    out_file.close()
