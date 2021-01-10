# -*- coding: utf-8 -*-
"""Helper for using URL library (urllib)."""

import urllib.error as urllib_error
import urllib.request as urllib_request

from l2tdevtools.lib import errors


class URLLibHelper(object):
  """URL library (urllib) helper."""

  def Request(self, url, post_data=None):
    """Sends a request to an URL.

    Args:
      url (str): URL to send the request.
      post_data (Optional[bytes]): data to send.

    Returns:
      bytes: response data.

    Raises:
      ConnectivityError: if the request failed.
    """
    request = urllib_request.Request(url)

    if post_data is not None:
      # This will change the request into a POST.
      request.data = post_data.encode('utf-8')

    try:
      url_object = urllib_request.urlopen(request)
    except urllib_error.HTTPError as exception:
      raise errors.ConnectivityError(
          'Failed requesting URL {0:s} with error: {1!s}'.format(
              url, exception))

    if url_object.code not in (200, 201):
      raise errors.ConnectivityError(
          'Failed requesting URL {0:s} with status code: {1:d}'.format(
              url, url_object.code))

    return url_object.read()
