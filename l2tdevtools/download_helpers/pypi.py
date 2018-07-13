# -*- coding: utf-8 -*-
"""Download helper object implementations."""

from __future__ import unicode_literals

import re

# pylint: disable=wrong-import-position
import pkg_resources

from l2tdevtools.download_helpers import project


class PyPIDownloadHelper(project.ProjectDownloadHelper):
  """Helps in downloading a PyPI code project."""

  def __init__(self, download_url):
    """Initializes the download helper.

    Args:
      download_url (str): download URL.

    Raises:
      ValueError: if download URL is not supported.
    """
    url_segments = download_url.split('/')
    if (len(url_segments) < 5 or url_segments[2] != 'pypi.org' or
        url_segments[3] != 'project'):
      raise ValueError('Unsupported download URL: {0:s}.'.format(
          download_url))

    super(PyPIDownloadHelper, self).__init__(download_url)
    self._project_name = url_segments[4]

  def GetLatestVersion(self, unused_project_name, version_definition):
    """Retrieves the latest version number for a given project name.

    Args:
      project_name (str): name of the project.
      version_definition (ProjectVersionDefinition): project version definition
          or None.

    Returns:
      str: latest version number or None if not available.
    """
    if version_definition:
      earliest_version = version_definition.GetEarliestVersion()
      if earliest_version and earliest_version[0] == '==':
        return '.'.join(earliest_version[1:])

    download_url = 'https://pypi.org/project/{0:s}#files'.format(
        self._project_name)

    page_content = self.DownloadPageContent(download_url)
    if not page_content:
      return None

    versions = {}
    expression_string = (
        r'"https://files.pythonhosted.org/packages/.*/.*/.*/'
        r'{0:s}-(?P<version>[\d\.\!]*(post\d+)?)'
        r'\.(tar\.bz2|tar\.gz|zip)"').format(self._project_name)

    for match in re.finditer(expression_string, page_content):
      version_string = match.group('version')
      if version_string:
        # We need to support PEP440 epoch versioning, which only newer versions
        # of setuptools support. So this is a bit of hack to handle epochs
        # but still use setuptools to handle most of the version matching.
        epoch, _, epoch_version_string = version_string.partition('!')
        if not epoch_version_string:
          # Per PEP440, if there is no epoch specified, the epoch is 0.
          epoch_version_string = epoch
          epoch = 0
        else:
          epoch = int(epoch, 10)

        # Note that pkg_resources.parse_version() returns an instance of
        # pkg_resources.SetuptoolsVersion.
        version_object = pkg_resources.parse_version(epoch_version_string)

        # Add the epoch to the version string for comparison.
        version_tuple = ((epoch, version_object), version_string)
        versions[version_tuple] = version_string

    latest_version = max(versions.keys())
    if latest_version:
      # Return the original string that defined the version
      return versions[latest_version]

    return None

  def GetDownloadURL(self, unused_project_name, project_version):
    """Retrieves the download URL for a given project name and version.

    Args:
      project_name (str): name of the project.
      project_version (str): version of the project.

    Returns:
      str: download URL of the project or None if not available.
    """
    download_url = 'https://pypi.org/project/{0:s}/{1!s}'.format(
        self._project_name, project_version)

    page_content = self.DownloadPageContent(download_url)
    if not page_content:
      return None

    # The format of the project download URL is:
    # https://files.pythonhosted.org/packages/.*/.*/.*/
    #     {project name}-{version}.{extension}
    expression_string = (
        '(https://files.pythonhosted.org/packages/.*/.*/.*/'
        '{0:s}-{1!s}[.](tar[.]bz2|tar[.]gz|zip))').format(
            self._project_name, project_version)
    matches = re.findall(expression_string, page_content)

    if not matches:
      return None

    return matches[0][0]

  def GetProjectIdentifier(self):
    """Retrieves the project identifier for a given project name.

    Returns:
      str: project identifier.
    """
    return 'org.pypi.{0:s}'.format(self._project_name)
