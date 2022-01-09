# -*- coding: utf-8 -*-
"""Download helper object implementations."""

import abc
import logging
import os

from l2tdevtools.download_helpers import interface


class ProjectDownloadHelper(interface.DownloadHelper):
  """Helps in downloading a project."""

  def __init__(self, download_url):
    """Initializes a download helper.

    Args:
      download_url (str): download URL.
    """
    super(ProjectDownloadHelper, self).__init__(download_url)
    self._project_name = None

  def _GetLatestVersion(
      self, earliest_version, latest_version, available_versions,
      with_epoch=False):
    """Determines the latest version from a list of available versions.

    Args:
      earliest_version (str): earliest version in the project version definition
          or None if not set.
      latest_version (str): latest version in the project version definition
          or None if not set.
      available_versions (dict[str, [int]]): available versions where
          the key is the original version string and the value the individual
          integers of the digits in the version string.
      with_epoch (Optional[bool]): True if the available versions start with
          an epoch number.

    Returns:
      str: download URL of the project or None if not available.
    """
    comparable_earliest_version = None
    if earliest_version:
      comparable_earliest_version = [
          int(digit) for digit in earliest_version[1:]]

    comparable_latest_version = None
    if latest_version:
      comparable_latest_version = [
          int(digit) for digit in latest_version[1:]]

    comparable_available_versions = []
    for version in available_versions.values():
      if with_epoch:
        comparable_available_versions.append(version[1:])
      else:
        comparable_available_versions.append(version)

    latest_match = None
    for match in comparable_available_versions:
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

      if latest_match is None:
        latest_match = match

      elif match > latest_match:
        latest_match = match

    if not latest_match:
      return None

    # Map the latest match value to its index within the dictionary and return
    # the version string which is stored as the key in within the available
    # versions dictionary.
    latest_match = comparable_available_versions.index(latest_match)

    # Convert the result of dict.keys() into a list for Python 3.
    return list(available_versions.keys())[latest_match]

  def Download(self, project_name, project_version):
    """Downloads the project for a given project name and version.

    Args:
    Args:
      project_name (str): name of the project.
      project_version (str): version of the project.

    Returns:
      str: filename if successful also if the file was already downloaded
          or None if not available.
    """
    download_url = self.GetDownloadURL(project_name, project_version)
    if not download_url:
      logging.warning('Unable to determine download URL for: {0:s}'.format(
          project_name))
      return None

    filename = self.DownloadFile(download_url)

    # GitHub archive package filenames can be:
    # {project version}.tar.gz
    # release-{project version}.tar.gz
    # v{project version}.tar.gz
    github_archive_filenames = [
        '{0!s}.tar.gz'.format(project_version),
        'release-{0!s}.tar.gz'.format(project_version),
        'v{0!s}.tar.gz'.format(project_version)]

    if filename in github_archive_filenames:
      # The desired source package filename is:
      # {project name}-{project version}.tar.gz
      package_filename = '{0:s}-{1:s}.tar.gz'.format(
          project_name, project_version)

      if os.path.exists(package_filename):
        os.remove(package_filename)

      os.rename(filename, package_filename)
      filename = package_filename

    return filename

  # pylint: disable=redundant-returns-doc
  @abc.abstractmethod
  def GetDownloadURL(self, project_name, project_version):
    """Retrieves the download URL for a given project name and version.

    Args:
      project_name (str): name of the project.
      project_version (str): version of the project.

    Returns:
      str: download URL of the project or None on error.
    """

  # pylint: disable=redundant-returns-doc
  @abc.abstractmethod
  def GetProjectIdentifier(self):
    """Retrieves the project identifier for a given project name.

    Returns:
      str: project identifier.
    """
