# -*- coding: utf-8 -*-
"""Download helper object implementations."""

from __future__ import unicode_literals

import abc
import logging
import os

from l2tdevtools.download_helpers import interface


class ProjectDownloadHelper(interface.DownloadHelper):
  """Helps in downloading a project."""

  def __init__(self, download_url):
    """Initializes the download helper.

    Args:
      download_url (str): download URL.
    """
    super(ProjectDownloadHelper, self).__init__(download_url)
    self._project_name = None

  def Download(self, project_name, project_version):
    """Downloads the project for a given project name and version.

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

  @abc.abstractmethod
  def GetDownloadURL(self, project_name, project_version):
    """Retrieves the download URL for a given project name and version.

    Args:
      project_name (str): name of the project.
      project_version (str): version of the project.

    Returns:
      str: download URL of the project or None on error.
    """

  @abc.abstractmethod
  def GetProjectIdentifier(self):
    """Retrieves the project identifier for a given project name.

    Returns:
      str: project identifier.
    """
