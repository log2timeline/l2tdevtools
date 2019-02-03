# -*- coding: utf-8 -*-
"""Helper related functions and classes for testing."""


class TestURLLibHelper(object):
  """URL library (urllib) helper for testing."""

  def __init__(self, result=b''):
    """Initializes an URL library (urllib) helper.

    Args:
      result (bytes): result that should be returned.
    """
    super(TestURLLibHelper, self).__init__()
    self._result = result

  # pylint: disable=unused-argument
  def Request(self, url, **unused_kwargs):
    """Sends a request to an URL.

    Args:
      url (str): URL to send the request.

    Returns:
      bytes: response data.

    Raises:
      ConnectivityError: if the request failed.
    """
    return self._result
