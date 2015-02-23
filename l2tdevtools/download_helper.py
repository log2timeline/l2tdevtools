# -*- coding: utf-8 -*-
"""Download helper object implementations."""

import abc
import io
import json
import logging
import os
import re
import urllib2

try:
  import ConfigParser as configparser
except ImportError:
  import configparser


class DownloadHelper(object):
  """Class that helps in downloading a project."""

  def __init__(self):
    """Initializes the download helper."""
    super(DownloadHelper, self).__init__()
    self._cached_url = u''
    self._cached_page_content = b''

  def Download(self, project_name, project_version):
    """Downloads the project for a given project name and version.

    Args:
      project_name: the name of the project.
      project_version: the version of the project.

    Returns:
      The filename if successful also if the file was already downloaded
      or None on error.
    """
    download_url = self.GetDownloadUrl(project_name, project_version)
    if not download_url:
      logging.warning(u'Unable to determine download URL for: {0:s}'.format(
          project_name))
      return

    return self.DownloadFile(download_url)

  def DownloadFile(self, download_url):
    """Downloads a file from the URL and returns the filename.

       The filename is extracted from the last part of the URL.

    Args:
      download_url: the URL where to download the file.

    Returns:
      The filename if successful also if the file was already downloaded
      or None on error.
    """
    _, _, filename = download_url.rpartition(u'/')

    if not os.path.exists(filename):
      logging.info(u'Downloading: {0:s}'.format(download_url))

      url_object = urllib2.urlopen(download_url)
      if url_object.code != 200:
        return

      file_object = open(filename, 'wb')
      file_object.write(url_object.read())
      file_object.close()

    return filename

  def DownloadPageContent(self, download_url):
    """Downloads the page content from the URL and caches it.

    Args:
      download_url: the URL where to download the page content.

    Returns:
      The page content if successful, None otherwise.
    """
    if not download_url:
      return

    if self._cached_url != download_url:
      url_object = urllib2.urlopen(download_url)

      if url_object.code != 200:
        return

      self._cached_page_content = url_object.read()
      self._cached_url = download_url

    return self._cached_page_content

  @abc.abstractmethod
  def GetDownloadUrl(self, project_name, project_version):
    """Retrieves the download URL for a given project name and version.

    Args:
      project_name: the name of the project.
      project_version: the version of the project.

    Returns:
      The download URL of the project or None on error.
    """

  @abc.abstractmethod
  def GetProjectIdentifier(self, project_name):
    """Retrieves the project identifier for a given project name.

    Args:
      project_name: the name of the project.

    Returns:
      The project identifier or None on error.
    """


class GoogleCodeWikiDownloadHelper(DownloadHelper):
  """Class that helps in downloading a wiki-based Google code project."""

  def GetLatestVersion(self, project_name):
    """Retrieves the latest version number for a given project name.

    Args:
      project_name: the name of the project.

    Returns:
      The a string containing the latest version number or None on error.
    """
    download_url = u'https://code.google.com/p/{0:s}/downloads/list'.format(
        project_name)

    page_content = self.DownloadPageContent(download_url)
    if not page_content:
      return

    # The format of the project download URL is:
    # href="//{project name}.googlecode.com/files/
    # {project name}-{version}.tar.gz
    expression_string = (
        u'href="//{0:s}.googlecode.com/files/'
        u'{0:s}-([0-9]+[.][0-9]+|[0-9]+[.][0-9]+[.][0-9]+)[.]tar[.]gz').format(
            project_name)
    matches = re.findall(expression_string, page_content)

    if not matches:
      return

    # Split the version string and convert every digit into an integer.
    # A string compare of both version strings will yield an incorrect result.
    matches = [map(int, match.split(u'.')) for match in matches]

    # Find the latest version number and transform it back into a string.
    return u'.'.join([u'{0:d}'.format(digit) for digit in max(matches)])

  def GetDownloadUrl(self, project_name, project_version):
    """Retrieves the download URL for a given project name and version.

    Args:
      project_name: the name of the project.
      project_version: the version of the project.

    Returns:
      The download URL of the project or None on error.
    """
    return (
        u'https://{0:s}.googlecode.com/files/{0:s}-{1:s}.tar.gz').format(
            project_name, project_version)

  def GetProjectIdentifier(self, project_name):
    """Retrieves the project identifier for a given project name.

    Args:
      project_name: the name of the project.

    Returns:
      The project identifier or None on error.
    """
    return u'com.google.code.p.{0:s}'.format(project_name)


class GithubReleasesDownloadHelper(DownloadHelper):
  """Class that helps in downloading a project with GitHub releases."""

  def __init__(self, organization):
    """Initializes the download helper.

    Args:
      organization: the github organization or user name.
    """
    super(GithubReleasesDownloadHelper, self).__init__()
    self.organization = organization

  def GetLatestVersion(self, project_name):
    """Retrieves the latest version number for a given project name.

    Args:
      project_name: the name of the project.

    Returns:
      The latest version number or 0 on error.
    """
    download_url = u'https://github.com/{0:s}/{1:s}/releases'.format(
        self.organization, project_name)

    page_content = self.DownloadPageContent(download_url)
    if not page_content:
      return 0

    # The format of the project download URL is:
    # /{organization}/{project name}/releases/download/{git tag}/
    # {project name}{status-}{version}.tar.gz
    # Note that the status is optional and will be: beta, alpha or experimental.
    expression_string = (
        u'/{0:s}/{1:s}/releases/download/[^/]*/{1:s}-[a-z-]*([0-9]+)'
        u'[.]tar[.]gz').format(self.organization, project_name)
    matches = re.findall(expression_string, page_content)

    if not matches:
      return 0

    return int(max(matches))

  def GetDownloadUrl(self, project_name, project_version):
    """Retrieves the download URL for a given project name and version.

    Args:
      project_name: the name of the project.
      project_version: the version of the project.

    Returns:
      The download URL of the project or None on error.
    """
    download_url = u'https://github.com/{0:s}/{1:s}/releases'.format(
        self.organization, project_name)

    page_content = self.DownloadPageContent(download_url)
    if not page_content:
      return

    # The format of the project download URL is:
    # /{organization}/{project name}/releases/download/{git tag}/
    # {project name}{status-}{version}.tar.gz
    # Note that the status is optional and will be: beta, alpha or experimental.
    expression_string = (
        u'/{0:s}/{1:s}/releases/download/[^/]*/{1:s}-[a-z-]*{2!s}'
        u'[.]tar[.]gz').format(self.organization, project_name, project_version)
    matches = re.findall(expression_string, page_content)

    if len(matches) != 1:
      # Try finding a match without the status in case the project provides
      # multiple versions with a different status.
      expression_string = (
          u'/{0:s}/{1:s}/releases/download/[^/]*/{1:s}-*{2!s}'
          u'[.]tar[.]gz').format(
              self.organization, project_name, project_version)
      matches = re.findall(expression_string, page_content)

    if not matches or len(matches) != 1:
      return

    return u'https://github.com{0:s}'.format(matches[0])

  def GetProjectIdentifier(self, project_name):
    """Retrieves the project identifier for a given project name.

    Args:
      project_name: the name of the project.

    Returns:
      The project identifier or None on error.
    """
    return u'com.github.{0:s}.{1:s}'.format(self.organization, project_name)


class GoogleDriveDownloadHelper(DownloadHelper):
  """Class that helps in downloading a Google Drive hosted project."""

  @abc.abstractmethod
  def GetGoogleDriveDownloadsUrl(self, project_name):
    """Retrieves the Google Drive Download URL.

    Args:
      project_name: the name of the project.

    Returns:
      The downloads URL or None on error.
    """

  def GetLatestVersion(self, project_name):
    """Retrieves the latest version number for a given project name.

    Args:
      project_name: the name of the project.

    Returns:
      The latest version number or 0 on error.
    """
    download_url = self.GetGoogleDriveDownloadsUrl(project_name)

    page_content = self.DownloadPageContent(download_url)
    if not page_content:
      return 0

    # The format of the project download URL is:
    # /host/{random string}/{project name}-{status-}{version}.tar.gz
    # Note that the status is optional and will be: beta, alpha or experimental.
    expression_string = u'/host/[^/]*/{0:s}-[a-z-]*([0-9]+)[.]tar[.]gz'.format(
        project_name)
    matches = re.findall(expression_string, page_content)

    if not matches:
      return 0

    return int(max(matches))

  def GetDownloadUrl(self, project_name, project_version):
    """Retrieves the download URL for a given project name and version.

    Args:
      project_name: the name of the project.
      project_version: the version of the project.

    Returns:
      The download URL of the project or None on error.
    """
    download_url = self.GetGoogleDriveDownloadsUrl(project_name)

    page_content = self.DownloadPageContent(download_url)
    if not page_content:
      return

    # The format of the project download URL is:
    # /host/{random string}/{project name}-{status-}{version}.tar.gz
    # Note that the status is optional and will be: beta, alpha or experimental.
    expression_string = u'/host/[^/]*/{0:s}-[a-z-]*{1!s}[.]tar[.]gz'.format(
        project_name, project_version)
    matches = re.findall(expression_string, page_content)

    if len(matches) != 1:
      # Try finding a match without the status in case the project provides
      # multiple versions with a different status.
      expression_string = u'/host/[^/]*/{0:s}-{1!s}[.]tar[.]gz'.format(
          project_name, project_version)
      matches = re.findall(expression_string, page_content)

    if not matches or len(matches) != 1:
      return

    return u'https://googledrive.com{0:s}'.format(matches[0])


# TODO: Merge with LibyalGithubReleasesDownloadHelper when Google Drive
# support is no longer needed.
# pylint: disable=abstract-method
class LibyalGitHubDownloadHelper(DownloadHelper):
  """Class that helps in downloading a libyal GitHub project."""

  def __init__(self):
    """Initializes the download helper."""
    super(LibyalGitHubDownloadHelper, self).__init__()
    self._download_helper = None

  def GetWikiConfigurationSourcePackageUrl(self, project_name):
    """Retrieves the source package URL from the libyal wiki configuration.

    Args:
      project_name: the name of the project.

    Returns:
      The source package URL or None on error.
    """
    download_url = (
        u'https://raw.githubusercontent.com/libyal/{0:s}/master/'
        u'{0:s}-wiki.ini').format(project_name)

    page_content = self.DownloadPageContent(download_url)
    if not page_content:
      return

    config_parser = configparser.RawConfigParser()
    config_parser.readfp(io.BytesIO(page_content))

    return json.loads(config_parser.get(u'source_package', u'url'))

  def GetLatestVersion(self, project_name):
    """Retrieves the latest version number for a given project name.

    Args:
      project_name: the name of the project.

    Returns:
      The latest version number or 0 on error.
    """
    if not self._download_helper:
      download_url = self.GetWikiConfigurationSourcePackageUrl(project_name)

      if download_url.startswith(u'https://github.com'):
        self._download_helper = LibyalGithubReleasesDownloadHelper()

      elif download_url.startswith(u'https://googledrive.com'):
        self._download_helper = LibyalGoogleDriveDownloadHelper(download_url)

    return self._download_helper.GetLatestVersion(project_name)

  def GetDownloadUrl(self, project_name, project_version):
    """Retrieves the download URL for a given project name and version.

    Args:
      project_name: the name of the project.
      project_version: the version of the project.

    Returns:
      The download URL of the project or None on error.
    """
    if not self._download_helper:
      download_url = self.GetWikiConfigurationSourcePackageUrl(project_name)

      if download_url.startswith(u'https://github.com'):
        self._download_helper = LibyalGithubReleasesDownloadHelper()

      elif download_url.startswith(u'https://googledrive.com'):
        self._download_helper = LibyalGoogleDriveDownloadHelper(download_url)

    return self._download_helper.GetDownloadUrl(project_name, project_version)


class LibyalGoogleDriveDownloadHelper(GoogleDriveDownloadHelper):
  """Class that helps in downloading a libyal project with Google Drive."""

  def __init__(self, google_drive_url):
    """Initializes the download helper.

    Args:
      google_drive_url: the project Google Drive URL.
    """
    super(LibyalGoogleDriveDownloadHelper, self).__init__()
    self._google_drive_url = google_drive_url

  def GetGoogleDriveDownloadsUrl(self, project_name):
    """Retrieves the Download URL from the GitHub project page.

    Args:
      project_name: the name of the project.

    Returns:
      The downloads URL or None on error.
    """
    return self._google_drive_url

  def GetProjectIdentifier(self, project_name):
    """Retrieves the project identifier for a given project name.

    Args:
      project_name: the name of the project.

    Returns:
      The project identifier or None on error.
    """
    return u'com.github.libyal.{0:s}'.format(project_name)


class LibyalGithubReleasesDownloadHelper(GithubReleasesDownloadHelper):
  """Class that helps in downloading a libyal project with GitHub releases."""

  def __init__(self):
    """Initializes the download helper."""
    super(LibyalGithubReleasesDownloadHelper, self).__init__(u'libyal')


class Log2TimelineGitHubDownloadHelper(GithubReleasesDownloadHelper):
  """Class that helps in downloading a log2timeline GitHub project."""

  def __init__(self):
    """Initializes the download helper."""
    super(Log2TimelineGitHubDownloadHelper, self).__init__(u'log2timeline')


class PyPiDownloadHelper(DownloadHelper):
  """Class that helps in downloading a pypi code project."""

  def GetLatestVersion(self, project_name):
    """Retrieves the latest version number for a given project name.

    Args:
      project_name: the name of the project.

    Returns:
      The a string containing the latest version number or None on error.
    """
    # TODO: add support to handle index of packages pages, e.g. for pyparsing.
    download_url = u'https://pypi.python.org/pypi/{0:s}'.format(project_name)

    page_content = self.DownloadPageContent(download_url)
    if not page_content:
      return

    # The format of the project download URL is:
    # https://pypi.python.org/packages/source/{first letter project name}/
    # {project name}/{project name}-{version}.tar.gz
    expression_string = (
        u'https://pypi.python.org/packages/source/{0:s}/{1:s}/'
        u'{1:s}-([0-9]+[.][0-9]+|[0-9]+[.][0-9]+[.][0-9]+)[.]tar[.]gz').format(
            project_name[0], project_name)
    matches = re.findall(expression_string, page_content)

    if not matches:
      return

    # Split the version string and convert every digit into an integer.
    # A string compare of both version strings will yield an incorrect result.
    matches = [map(int, match.split(u'.')) for match in matches]

    # Find the latest version number and transform it back into a string.
    return u'.'.join([u'{0:d}'.format(digit) for digit in max(matches)])

  def GetDownloadUrl(self, project_name, project_version):
    """Retrieves the download URL for a given project name and version.

    Args:
      project_name: the name of the project.
      project_version: the version of the project.

    Returns:
      The download URL of the project or None on error.
    """
    return (
        u'https://pypi.python.org/packages/source/{0:s}/{1:s}/'
        u'{1:s}-{2:s}.tar.gz').format(
            project_name[0], project_name, project_version)

  def GetProjectIdentifier(self, project_name):
    """Retrieves the project identifier for a given project name.

    Args:
      project_name: the name of the project.

    Returns:
      The project identifier or None on error.
    """
    return u'org.python.pypi.{0:s}'.format(project_name)


class SourceForgeDownloadHelper(DownloadHelper):
  """Class that helps in downloading a Source Forge project."""

  def GetLatestVersion(self, project_name):
    """Retrieves the latest version number for a given project name.

    Args:
      project_name: the name of the project.

    Returns:
      The a string containing the latest version number or None on error.
    """
    # TODO: make this more robust to detect different naming schemes.
    download_url = u'http://sourceforge.net/projects/{0:s}/files/{0:s}/'.format(
        project_name)

    page_content = self.DownloadPageContent(download_url)
    if not page_content:
      return 0

    # The format of the project download URL is:
    # /projects/{project name}/files/{project name}/{project name}-{version}/
    expression_string = (
        u'<a href="/projects/{0:s}/files/{0:s}/'
        u'{0:s}-([0-9]+[.][0-9]+[.][0-9]+)/"').format(project_name)
    matches = re.findall(expression_string, page_content)

    if not matches:
      return 0

    numeric_matches = [u''.join(match.split(u'.')) for match in matches]
    return matches[numeric_matches.index(max(numeric_matches))]

  def GetDownloadUrl(self, project_name, project_version):
    """Retrieves the download URL for a given project name and version.

    Args:
      project_name: the name of the project.
      project_version: the version of the project.

    Returns:
      The download URL of the project or None on error.
    """
    return (
        u'http://downloads.sourceforge.net/project/{0:s}/{0:s}/{0:s}-{1:s}'
        u'/{0:s}-{1:s}.tar.gz').format(project_name, project_version)

  def GetProjectIdentifier(self, project_name):
    """Retrieves the project identifier for a given project name.

    Args:
      project_name: the name of the project.

    Returns:
      The project identifier or None on error.
    """
    return u'net.sourceforge.projects.{0:s}'.format(project_name)
