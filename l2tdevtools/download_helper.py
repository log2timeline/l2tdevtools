# -*- coding: utf-8 -*-
"""Download helper object implementations."""

from __future__ import unicode_literals

from l2tdevtools.download_helpers import github
from l2tdevtools.download_helpers import pypi
from l2tdevtools.download_helpers import sourceforge


class DownloadHelperFactory(object):
  """Factory class for download helpers."""

  @classmethod
  def NewDownloadHelper(cls, download_url):
    """Creates a new download helper.

    Args:
      download_url (str): download URL.

    Returns:
      DownloadHelper: download helper or None if no corresponding helper
          could be found for the download URL.
    """
    if download_url.endswith('/'):
      download_url = download_url[:-1]

    # Unify http:// and https:// URLs for the download helper check.
    if download_url.startswith('https://'):
      download_url = 'http://{0:s}'.format(download_url[8:])

    # Remove URL arguments.
    download_url, _, _ = download_url.partition('?')

    if download_url.startswith('http://pypi.org/project/'):
      download_helper_class = pypi.PyPIDownloadHelper

    elif (download_url.startswith('http://sourceforge.net/projects/') and
          download_url.endswith('/files')):
      download_helper_class = sourceforge.SourceForgeDownloadHelper

    elif (download_url.startswith('http://github.com/') and
          download_url.endswith('/releases')):
      download_helper_class = github.GitHubReleasesDownloadHelper

    else:
      download_helper_class = None

    if not download_helper_class:
      return None

    return download_helper_class(download_url)
