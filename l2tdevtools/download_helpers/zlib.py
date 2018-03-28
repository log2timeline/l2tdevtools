# -*- coding: utf-8 -*-
"""Download helper object implementations."""

from __future__ import unicode_literals

import re

from l2tdevtools.download_helpers import project


class ZlibDownloadHelper(project.ProjectDownloadHelper):
  """Helps in downloading the zlib project."""

  def __init__(self, download_url):
    """Initializes the download helper.

    Args:
      download_url (str): download URL.

    Raises:
      ValueError: if download URL is not supported.
    """
    url_segments = download_url.split('/')
    if len(url_segments) < 3 or url_segments[2] != 'www.zlib.net':
      raise ValueError('Unsupported download URL.')

    super(ZlibDownloadHelper, self).__init__(download_url)
    self._project_name = 'zlib'

  def GetLatestVersion(self, unused_project_name, unused_version_definition):
    """Retrieves the latest version number for a given project name.

    Args:
      project_name (str): name of the project.
      version_definition (ProjectVersionDefinition): project version definition
          or None.

    Returns:
      str: latest version number or None if not available.
    """
    download_url = 'http://www.zlib.net'

    page_content = self.DownloadPageContent(download_url)
    if not page_content:
      return None

    # The format of the project download URL is:
    # http://zlib.net/{project name}-{version}.tar.gz
    expression_string = (
        '<A HREF="{0:s}-([0-9]+.[0-9]+.[0-9]+).tar.gz"').format(
            self._project_name)
    matches = re.findall(expression_string, page_content)

    if not matches:
      return None

    numeric_matches = [''.join(match.split('.')) for match in matches]
    return matches[numeric_matches.index(max(numeric_matches))]

  def GetDownloadURL(self, unused_project_name, project_version):
    """Retrieves the download URL for a given project name and version.

    Args:
      project_name (str): name of the project.
      project_version (str): version of the project.

    Returns:
      The download URL of the project or None if not available.
    """
    # The format of the project download URL is:
    # http://zlib.net/{project name}-{version}.tar.gz
    return 'http://zlib.net/{0:s}-{1:s}.tar.gz'.format(
        self._project_name, project_version)

  def GetProjectIdentifier(self):
    """Retrieves the project identifier for a given project name.

    Returns:
      str: project identifier.
    """
    return 'net.zlib.{0:s}'.format(self._project_name)
