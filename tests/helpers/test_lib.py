# -*- coding: utf-8 -*-
"""Helper related functions and classes for testing."""

class TestURLLibHelper(object):
  """URL library (urllib) helper for testing."""

  def __init__(self, result=True):
    """Initializes an URL library (urllib) helper.

    Args:
      result (bool): result that should be returned.
    """
    super(TestURLLibHelper, self).__init__()
    self._result = result

  def Request(self, unused_url, **unused_kwargs):
    """Sends a request to an URL.

    Args:
      url (str): URL to send the request.
      data (Optional[bytes]): data to send.

    Returns:
      bytes: response data.

    Raises:
      ConnectionError: if the request failed.
    """
    return b''
