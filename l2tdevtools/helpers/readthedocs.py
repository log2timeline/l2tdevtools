# -*- coding: utf-8 -*-
"""Helper for interacting with readthedocs."""

from __future__ import unicode_literals

import logging

from l2tdevtools.helpers import url_lib
from l2tdevtools.lib import errors


class ReadTheDocsHelper(object):
  """Readthedocs helper."""

  def __init__(self, project):
    """Initializes a readthedocs helper.

    Args:
      project (str): github project name.
    """
    super(ReadTheDocsHelper, self).__init__()
    self._project = project
    self._url_lib_helper = url_lib.URLLibHelper()

  def TriggerBuild(self):
    """Triggers readthedocs to build the docs of the project.

    Returns:
      bool: True if the build was triggered.
    """
    readthedocs_url = 'https://readthedocs.org/build/{0:s}'.format(
        self._project)

    try:
      self._url_lib_helper.Request(readthedocs_url, post_data=b'')

    except errors.ConnectivityError as exception:
      logging.warning('{0!s}'.format(exception))
      return False

    return True
