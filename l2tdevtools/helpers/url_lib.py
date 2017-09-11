# -*- coding: utf-8 -*-
"""Helper for using URL library (urllib)."""

import sys

# pylint: disable=import-error,no-name-in-module
if sys.version_info[0] < 3:
  import urllib2 as urllib_error
  import urllib2 as urllib_request
else:
  import urllib.error as urllib_error
  import urllib.request as urllib_request

from l2tdevtools.lib import errors  # pylint: disable=wrong-import-position


class URLLibHelper(object):
  """URL library (urllib) helper."""

  def Request(self, url, post_data=None):
    """Sends a request to an URL.

    Args:
      url (str): URL to send the request.
      data (Optional[bytes]): data to send.

    Returns:
      bytes: response data.

    Raises:
      ConnectionError: if the request failed.
    """
    request = urllib_request.Request(url)

    if post_data is not None:
      # This will change the request into a POST.
      request.add_data(post_data)

    try:
      url_object = urllib_request.urlopen(request)
    except urllib_error.HTTPError as exception:
      raise errors.ConnectionError(
          u'Failed triggering build with error: {0!s}'.format(exception))

    if url_object.code not in (200, 201):
      raise errors.ConnectionError(
          u'Failed triggering build with status code: {0:d}'.format(
              url_object.code))

    return url_object.read()
