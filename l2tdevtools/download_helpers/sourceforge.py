# -*- coding: utf-8 -*-
"""Download helper object implementations."""

from __future__ import unicode_literals

import re

from l2tdevtools.download_helpers import project


class SourceForgeDownloadHelper(project.ProjectDownloadHelper):
  """Helps in downloading a Source Forge project."""

  def __init__(self, download_url):
    """Initializes the download helper.

    Args:
      download_url (str): download URL.

    Raises:
      ValueError: if download URL is not supported.
    """
    url_segments = download_url.split('/')
    if (len(url_segments) < 5 or url_segments[2] != 'sourceforge.net' or
        url_segments[3] != 'projects' or url_segments[5] != 'files'):
      raise ValueError('Unsupported download URL.')

    super(SourceForgeDownloadHelper, self).__init__(download_url)
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

    # TODO: make this more robust to detect different naming schemes.
    download_url = (
        'https://sourceforge.net/projects/{0:s}/files/{0:s}/').format(
            self._project_name)

    page_content = self.DownloadPageContent(download_url)
    if not page_content:
      return None

    if self._project_name == 'pyparsing':
      # The format of the project download URL is:
      # /projects/{project name}/files/{project name}/{project name}-{version}/
      expression_string = (
          '<a href="/projects/{0:s}/files/{0:s}/'
          '{0:s}-([0-9]+[.][0-9]+[.][0-9]+)/"').format(
              self._project_name)
      matches = re.findall(expression_string, page_content)

    elif self._project_name == 'pywin32':
      # The format of the project download URL is:
      # /projects/{project name}/files/{project name}/Build%20{version}/
      expression_string = (
          '<a href="/projects/{0:s}/files/{0:s}/Build%20([0-9]+)/"').format(
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
    # TODO: make this more robust to detect different naming schemes.
    download_url = (
        'https://sourceforge.net/projects/{0:s}/files/{0:s}/').format(
            self._project_name)

    page_content = self.DownloadPageContent(download_url)
    if not page_content:
      return None

    download_url = None
    if self._project_name == 'pyparsing':
      # The format of the project download URL is:
      # /projects/{project name}/files/{project name}/{project name}-{version}/
      expression_string = (
          '<a href="/projects/{0:s}/files/{0:s}/{0:s}-({1:s})/"').format(
              self._project_name, project_version)
      matches = re.findall(expression_string, page_content)

      if matches:
        download_url = (
            'https://downloads.sourceforge.net/project/{0:s}/{0:s}/{0:s}-{1:s}'
            '/{0:s}-{1:s}.tar.gz').format(
                self._project_name, project_version)

    elif self._project_name == 'pywin32':
      # The format of the project download URL is:
      # /projects/{project name}/files/{project name}/Build%20{version}/
      expression_string = (
          '<a href="/projects/{0:s}/files/{0:s}/Build%20({1:s})/"').format(
              self._project_name, project_version)
      matches = re.findall(expression_string, page_content)

      if matches:
        download_url = (
            'https://downloads.sourceforge.net/project/{0:s}/{0:s}'
            '/Build%20{1:s}/{0:s}-{1:s}.zip').format(
                self._project_name, project_version)

    return download_url

  def GetProjectIdentifier(self):
    """Retrieves the project identifier for a given project name.

    Returns:
      str: project identifier.
    """
    return 'net.sourceforge.projects.{0:s}'.format(self._project_name)
