# -*- coding: utf-8 -*-
"""Download helper object implementations."""

from __future__ import unicode_literals

import json
import re

from l2tdevtools.download_helpers import project


class GitHubReleasesDownloadHelper(project.ProjectDownloadHelper):
  """Helps in downloading a project with GitHub releases."""

  _VERSION_EXPRESSIONS = [
      '[0-9]+',
      '[0-9]+[.][0-9]+',
      '[0-9]+[.][0-9]+[.][0-9]+',
      'release-[0-9]+[.][0-9]+[.][0-9]+',
      'v[0-9]+[.][0-9]',
      'v[0-9]+[.][0-9]+[.][0-9]+',
      '[0-9]+[.][0-9]+[.][0-9]+[-][0-9]+']

  def __init__(self, download_url):
    """Initializes the download helper.

    Args:
      download_url (str): download URL.

    Raises:
      ValueError: if download URL is not supported.
    """
    url_segments = download_url.split('/')
    if len(url_segments) < 5 or url_segments[2] != 'github.com':
      raise ValueError('Unsupported download URL.')

    super(GitHubReleasesDownloadHelper, self).__init__(download_url)
    self._organization = url_segments[3]
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

    for version_string in version_strings:
      if not version_string:
        continue

      # Remove a leading 'release-'.
      if version_string.startswith('release-'):
        version_string = version_string[8:]

      # Remove a leading 'v'.
      elif version_string.startswith('v'):
        version_string = version_string[1:]

      # Some versions contain '-' as the release number separator for the split
      # we want this to be '.'.
      comparable_version = version_string.replace('-', '.')

      # Convert the result of map() into a list for Python 3.
      comparable_version = list(map(int, comparable_version.split('.')))
      available_versions[version_string] = comparable_version

    return available_versions

  def GetLatestVersionWithAPI(self, version_definition):
    """Uses the GitHub API to retrieve the latest version number for a project.

    This method is intended for use in tests only, due to the API rate-limit.

    Args:
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

    github_url = 'https://api.github.com/repos/{0:s}/{1:s}/releases'.format(
        self._organization, self._repository)
    page_content = self.DownloadPageContent(github_url)
    if not page_content:
      return None

    api_response = json.loads(page_content)
    release_names = [release['name'] for release in api_response]

    expression_string = '({0:s})'.format('|'.join(self._VERSION_EXPRESSIONS))
    versions = []
    for release in release_names:
      version_strings = re.findall(expression_string, release)
      versions.extend(version_strings)

    available_versions = self._GetAvailableVersions(versions)
    return self._GetLatestVersion(
        earliest_version, latest_version, available_versions)

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
    # /{organization}/{repository}/releases/download/{git tag}/
    # {project name}{status-}{version}.tar.gz
    # Note that the status is optional and will be: beta, alpha or experimental.
    # E.g. used by libyal.
    expression_string = (
        '/{0:s}/{1:s}/releases/download/[^/]*/{2:s}-[a-z-]*({3:s})'
        '[.]tar[.]gz[^.]').format(
            self._organization, self._repository, project_name,
            '|'.join(self._VERSION_EXPRESSIONS))
    matches = re.findall(expression_string, page_content, flags=re.IGNORECASE)

    if not matches:
      # The format of the project archive download URL is:
      # /{organization}/{repository}/archive/{version}.tar.gz
      expression_string = (
          '/{0:s}/{1:s}/archive/({2:s})[.]tar[.]gz[^.]').format(
              self._organization, self._repository,
              '|'.join(self._VERSION_EXPRESSIONS))
      matches = re.findall(expression_string, page_content, flags=re.IGNORECASE)

    if not matches:
      # The format of the project archive download URL is:
      # /{organization}/{repository}/archive/{project name}-{version}.tar.gz
      expression_string = (
          '/{0:s}/{1:s}/archive/{2:s}[-]({3:s})[.]tar[.]gz[^.]').format(
              self._organization, self._repository, project_name,
              '|'.join(self._VERSION_EXPRESSIONS))
      matches = re.findall(expression_string, page_content, flags=re.IGNORECASE)

      # TODO: this check will fail if the case in the URL is different.
      # Make checks case insensitive.

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
    # /{organization}/{repository}/releases/download/{git tag}/
    # {project name}{status-}{version}.tar.gz
    # Note that the status is optional and will be: beta, alpha or experimental.
    expression_string = (
        '/{0:s}/{1:s}/releases/download/[^/]*/{2:s}-[a-z-]*{3!s}'
        '[.]tar[.]gz[^.]').format(
            self._organization, self._repository, project_name, project_version)
    matches = re.findall(expression_string, page_content, flags=re.IGNORECASE)

    if len(matches) != 1:
      # Try finding a match without the status in case the project provides
      # multiple versions with a different status.
      expression_string = (
          '/{0:s}/{1:s}/releases/download/[^/]*/{2:s}-*{3!s}'
          '[.]tar[.]gz[^.]').format(
              self._organization, self._repository, project_name,
              project_version)
      matches = re.findall(expression_string, page_content, flags=re.IGNORECASE)

    if matches and len(matches) == 1:
      return 'https://github.com{0:s}'.format(matches[0][:-1])

    if matches and len(matches) != 1:
      return None

    # The format of the project archive download URL is:
    # /{organization}/{repository}/archive/{version}.tar.gz
    expression_string = (
        '/{0:s}/{1:s}/archive/{2!s}[.]tar[.]gz[^.]').format(
            self._organization, self._repository, project_version)
    matches = re.findall(expression_string, page_content, flags=re.IGNORECASE)

    if matches and len(matches) == 1:
      return 'https://github.com{0:s}'.format(matches[0][:-1])

    if len(matches) != 1:
      # The format of the project archive download URL is:
      # /{organization}/{repository}/archive/release-{version}.tar.gz
      expression_string = (
          '/{0:s}/{1:s}/archive/release-{2!s}[.]tar[.]gz[^.]').format(
              self._organization, self._repository, project_version)
      matches = re.findall(expression_string, page_content, flags=re.IGNORECASE)

    if matches and len(matches) == 1:
      return 'https://github.com{0:s}'.format(matches[0][:-1])

    if len(matches) != 1:
      # The format of the project archive download URL is:
      # /{organization}/{repository}/archive/v{version}.tar.gz
      expression_string = (
          '/{0:s}/{1:s}/archive/v{2!s}[.]tar[.]gz[^.]').format(
              self._organization, self._repository, project_version)
      matches = re.findall(expression_string, page_content, flags=re.IGNORECASE)

    if matches and len(matches) == 1:
      return 'https://github.com{0:s}'.format(matches[0][:-1])

    if len(matches) != 1:
      # The format of the project archive download URL is:
      # /{organization}/{repository}/archive/{project name}-{version}.tar.gz
      expression_string = (
          '/{0:s}/{1:s}/archive/{2:s}[-]{3!s}[.]tar[.]gz[^.]').format(
              self._organization, self._repository, project_name,
              project_version)
      matches = re.findall(expression_string, page_content, flags=re.IGNORECASE)

    if matches and len(matches) == 1:
      return 'https://github.com{0:s}'.format(matches[0][:-1])

    return None

  def GetProjectIdentifier(self):
    """Retrieves the project identifier for a given project name.

    Returns:
      str: project identifier.
    """
    return 'com.github.{0:s}.{1:s}'.format(
        self._organization, self._repository)
