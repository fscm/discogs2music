# -*- coding: UTF-8 -*-
#
# copyright: 2020-2021, Frederico Martins
# author: Frederico Martins <http://github.com/fscm>
# license: SPDX-License-Identifier: MIT

"""Update your Music app albums or songs rating with your Discogs
ratings.
"""

import sys
from .discogs2music import main


if __name__ == '__main__':
  sys.exit(main())
