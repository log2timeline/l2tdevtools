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

    response_code = None
    page_content = None

    try:
      with urllib_request.urlopen(request) as url_object:
        response_code = url_object.code
        if response_code in (200, 201):
          page_content = url_object.read()

    except urllib_error.HTTPError as exception:
      raise errors.ConnectivityError(
          'Failed requesting URL {0:s} with error: {1!s}'.format(
              url, exception))

    if response_code not in (200, 201):
      raise errors.ConnectivityError(
          'Failed requesting URL {0:s} with status code: {1:d}'.format(
              url, response_code))

    return page_content
