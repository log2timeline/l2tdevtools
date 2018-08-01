# -*- coding: utf-8 -*-
"""Download helper object implementations."""

from __future__ import unicode_literals

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

  def GetLatestVersion(self, project_name, version_definition):
    """Retrieves the latest version number for a given project name.

    Args:
      project_name (str): name of the project.
      version_definition (ProjectVersionDefinition): project version definition
          or None.

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
    matches = re.findall(expression_string, page_content)

    if not matches:
      # The format of the project archive download URL is:
      # /{organization}/{repository}/archive/{version}.tar.gz
      expression_string = (
          '/{0:s}/{1:s}/archive/({2:s})[.]tar[.]gz[^.]').format(
              self._organization, self._repository,
              '|'.join(self._VERSION_EXPRESSIONS))
      matches = re.findall(expression_string, page_content)

    if not matches:
      # The format of the project archive download URL is:
      # /{organization}/{repository}/archive/{project name}-{version}.tar.gz
      expression_string = (
          '/{0:s}/{1:s}/archive/{2:s}[-]({3:s})[.]tar[.]gz[^.]').format(
              self._organization, self._repository, project_name,
              '|'.join(self._VERSION_EXPRESSIONS))
      matches = re.findall(expression_string, page_content)

      # TODO: this check will fail if the case in the URL is different.
      # Make checks case insenstive.

    if not matches:
      return None

    # Split the version string and convert every digit into an integer.
    # A string compare of both version strings will yield an incorrect result.
    comparable_matches = {}

    for match in matches:
      # Remove a leading 'release-'.
      if match.startswith('release-'):
        match = match[8:]
      # Remove a leading 'v'.
      elif match.startswith('v'):
        match = match[1:]

      # Some versions contain '-' as the release number separator for the split
      # we want this to be '.'.
      comparable_match = match.replace('-', '.')

      # Convert the result of map() into a list for Python 3.
      comparable_match = list(map(int, comparable_match.split('.')))
      comparable_matches[match] = comparable_match

    # Find the latest version number.
    comparable_earliest_version = None
    if earliest_version:
      comparable_earliest_version = [
          int(digit) for digit in earliest_version[1:]]

    comparable_latest_version = None
    if latest_version:
      comparable_latest_version = [
          int(digit) for digit in latest_version[1:]]

    comparable_matching_versions = list(comparable_matches.values())

    latest_match = None
    for match in comparable_matching_versions:
      if latest_match is None:
        latest_match = match
        continue

      if earliest_version is not None:
        if earliest_version[0] == '>' and match <= comparable_earliest_version:
          continue

        if earliest_version[0] == '>=' and match < comparable_earliest_version:
          continue

      if latest_version is not None:
        if latest_version[0] == '<' and match >= comparable_latest_version:
          continue

        if latest_version[0] == '<=' and match > comparable_latest_version:
          continue

      if match > latest_match:
        latest_match = match

    # Map the latest match value to its index within the dictionary.
    # Convert the result of dict.values() into a list for Python 3.
    latest_match = comparable_matching_versions.index(latest_match)

    # Return the original version string which is stored as the key in within
    # the dictionary.
    # Convert the result of dict.keys() into a list for Python 3.
    return list(comparable_matches.keys())[latest_match]

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
    matches = re.findall(expression_string, page_content)

    if len(matches) != 1:
      # Try finding a match without the status in case the project provides
      # multiple versions with a different status.
      expression_string = (
          '/{0:s}/{1:s}/releases/download/[^/]*/{2:s}-*{3!s}'
          '[.]tar[.]gz[^.]').format(
              self._organization, self._repository, project_name,
              project_version)
      matches = re.findall(expression_string, page_content)

    if matches and len(matches) == 1:
      return 'https://github.com{0:s}'.format(matches[0][:-1])

    if matches and len(matches) != 1:
      return None

    # The format of the project archive download URL is:
    # /{organization}/{repository}/archive/{version}.tar.gz
    expression_string = (
        '/{0:s}/{1:s}/archive/{2!s}[.]tar[.]gz[^.]').format(
            self._organization, self._repository, project_version)
    matches = re.findall(expression_string, page_content)

    if matches and len(matches) == 1:
      return 'https://github.com{0:s}'.format(matches[0][:-1])

    if len(matches) != 1:
      # The format of the project archive download URL is:
      # /{organization}/{repository}/archive/release-{version}.tar.gz
      expression_string = (
          '/{0:s}/{1:s}/archive/release-{2!s}[.]tar[.]gz[^.]').format(
              self._organization, self._repository, project_version)
      matches = re.findall(expression_string, page_content)

    if matches and len(matches) == 1:
      return 'https://github.com{0:s}'.format(matches[0][:-1])

    if len(matches) != 1:
      # The format of the project archive download URL is:
      # /{organization}/{repository}/archive/v{version}.tar.gz
      expression_string = (
          '/{0:s}/{1:s}/archive/v{2!s}[.]tar[.]gz[^.]').format(
              self._organization, self._repository, project_version)
      matches = re.findall(expression_string, page_content)

    if matches and len(matches) == 1:
      return 'https://github.com{0:s}'.format(matches[0][:-1])

    if len(matches) != 1:
      # The format of the project archive download URL is:
      # /{organization}/{repository}/archive/{project name}-{version}.tar.gz
      expression_string = (
          '/{0:s}/{1:s}/archive/{2:s}[-]{3!s}[.]tar[.]gz[^.]').format(
              self._organization, self._repository, project_name,
              project_version)
      matches = re.findall(expression_string, page_content)

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
