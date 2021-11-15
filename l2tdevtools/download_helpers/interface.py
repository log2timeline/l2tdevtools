# -*- coding: utf-8 -*-
"""Download helper object implementations."""

import logging
import os

import urllib.error as urllib_error
import urllib.request as urllib_request


class DownloadHelper(object):
  """Helps in downloading files and web content."""

  def __init__(self, download_url):
    """Initializes a download helper.

    Args:
      download_url (str): download URL.
    """
    super(DownloadHelper, self).__init__()
    self._cached_url = ''
    self._cached_page_content = b''
    self._download_url = download_url

  def DownloadFile(self, download_url):
    """Downloads a file from the URL and returns the filename.

    The filename is extracted from the last part of the URL.

    Args:
      download_url (str): URL where to download the file.

    Returns:
      str: filename if successful also if the file was already downloaded
          or None if not available.
    """
    _, _, filename = download_url.rpartition('/')

    if not os.path.exists(filename):
      logging.info('Downloading: {0:s}'.format(download_url))

      try:
        with urllib_request.urlopen(download_url) as url_object:
          if url_object.code != 200:
            logging.warning(
                'Unable to download URL: {0:s} with status code: {1:d}'.format(
                    download_url, url_object.code))
            return None

          page_content = url_object.read()
          with open(filename, 'wb') as file_object:
            file_object.write(page_content)

      except urllib_error.URLError as exception:
        logging.warning(
            'Unable to download URL: {0:s} with error: {1!s}'.format(
                download_url, exception))
        return None

    return filename

  def DownloadPageContent(self, download_url, encoding='utf-8'):
    """Downloads the page content from the URL and caches it.

    Args:
      download_url (str): URL where to download the page content.
      encoding (Optional[str]): encoding of the page content, where None
          represents no encoding (or binary data).

    Returns:
      str: page content if successful or None if not available.
    """
    if not download_url:
      return None

    if self._cached_url != download_url:
      try:
        with urllib_request.urlopen(download_url) as url_object:
          if url_object.code != 200:
            return None

          page_content = url_object.read()

      except urllib_error.URLError as exception:
        logging.warning(
            'Unable to download URL: {0:s} with error: {1!s}'.format(
                download_url, exception))
        return None

      if encoding and isinstance(page_content, bytes):
        page_content = page_content.decode(encoding)

      self._cached_page_content = page_content
      self._cached_url = download_url

    return self._cached_page_content
