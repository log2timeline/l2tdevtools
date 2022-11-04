# -*- coding: utf-8 -*-
"""Download helper object implementations."""

import re

from l2tdevtools.download_helpers import project


class GitHubReleasesDownloadHelper(project.ProjectDownloadHelper):
  """Helps in downloading a project with GitHub releases."""

  def __init__(
      self, download_url, release_prefix=None, release_tag_prefix=None):
    """Initializes the download helper.

    Args:
      download_url (str): download URL.
      release_prefix (Optional[str]): release prefix.
      release_tag_prefix (Optional[str]): release tag prefix.

    Raises:
      ValueError: if download URL is not supported.
    """
    url_segments = download_url.split('/')
    if len(url_segments) < 5 or url_segments[2] != 'github.com':
      raise ValueError('Unsupported download URL.')

    super(GitHubReleasesDownloadHelper, self).__init__(download_url)
    self._organization = url_segments[3]
    self._release_prefix = release_prefix or ''
    self._release_tag_prefix = release_tag_prefix or ''
    self._repository = url_segments[4]

  def _GetAvailableVersions(self, version_strings):
    """Determines the available versions from version string matched.

    This function will split the version string and convert every digit into
    an integer. These lists of integers allow us to reliably compare versions.
    A string compare of version strings will yield an incorrect result.

    Args:
      version_strings (list[str]): version strings.

    Returns:
      dict[str, [int]]: available versions where the key is the original
          version string and the value the individual integers of
          the digits in the version string.
    """
    available_versions = {}

    release_tag_prefix_length = len(self._release_tag_prefix)

    for version_string in version_strings:
      if not version_string:
        continue

      if (self._release_tag_prefix and
          version_string.startswith(self._release_tag_prefix)):
        version_string = version_string[release_tag_prefix_length:]

      # Some versions contain '-' as the release number separator for the split
      # we want this to be '.'.
      comparable_version = version_string.replace('-', '.')

      # Convert the result of map() into a list for Python 3.
      comparable_version = list(map(int, comparable_version.split('.')))
      available_versions[version_string] = comparable_version

    return available_versions

  # pylint: disable=unused-argument
  def GetLatestVersion(self, project_name, version_definition):
    """Retrieves the latest version number for a given project name.

    Args:
      project_name (str): name of the project.
      version_definition (ProjectVersionDefinition): project version definition
          or None if not set.

    Returns:
      str: latest version number or None if not available.
    """
    earliest_version = None
    latest_version = None

    if version_definition:
      earliest_version = version_definition.GetEarliestVersion()
      if earliest_version and earliest_version[0] == '==':
        return '.'.join(earliest_version[1:])

      latest_version = version_definition.GetLatestVersion()

    download_url = 'https://github.com/{0:s}/{1:s}/releases'.format(
        self._organization, self._repository)

    page_content = self.DownloadPageContent(download_url)
    if not page_content:
      return None

    # The format of the project download URL is:
    # <a href="/{organization}/{repository}/releases/tag/{git tag}"
    expression_string = (
        '<a href="/{0:s}/{1:s}/releases/tag/([^"]*)"[^>]*>[^<]*</a>').format(
            self._organization, self._repository)
    matches = re.findall(expression_string, page_content, flags=re.IGNORECASE)

    if not matches:
      return None

    available_versions = self._GetAvailableVersions(matches)
    return self._GetLatestVersion(
        earliest_version, latest_version, available_versions)

  def GetDownloadURL(self, project_name, project_version):
    """Retrieves the download URL for a given project name and version.

    Args:
      project_name (str): name of the project.
      project_version (str): version of the project.

    Returns:
      str: download URL of the project or None if not available.
    """
    # TODO: add support for URL arguments '?after=release-2.2.0'
    download_url = 'https://github.com/{0:s}/{1:s}/releases'.format(
        self._organization, self._repository)

    page_content = self.DownloadPageContent(download_url)
    if not page_content:
      return None

    # The format of the project download URL is:
    # <a href="/{organization}/{repository}/releases/tag/{git tag}"
    expression_string = (
        '<a href="/{0:s}/{1:s}/releases/tag/{2:s}(.*{3!s}[^"]*)"[^>]*>([^<]*)'
        '</a>').format(
            self._organization, self._repository, self._release_tag_prefix,
            project_version)

    matches = re.findall(expression_string, page_content, flags=re.IGNORECASE)

    if matches and len(matches) == 1:
      version = matches[0][0]
      if self._release_prefix:
        release = '{0:s}{1:s}.tar.gz'.format(self._release_prefix, version)
      else:
        release = '{0:s}.tar.gz'.format(matches[0][1].replace(' ', '-'))

      return (
          'https://github.com/{0:s}/{1:s}/releases/download/{2:s}{3!s}/'
          '{4:s}').format(
              self._organization, self._repository, self._release_tag_prefix,
              version, release)

    return None

  def GetProjectIdentifier(self):
    """Retrieves the project identifier for a given project name.

    Returns:
      str: project identifier.
    """
    return 'com.github.{0:s}.{1:s}'.format(
        self._organization, self._repository)
