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
  import configparser  # pylint: disable=import-error


class DownloadHelper(object):
  """Class that helps in downloading files and web content."""

  def __init__(self, download_url):
    """Initializes the download helper.

    Args:
      download_url: a string containing the download URL.
    """
    super(DownloadHelper, self).__init__()
    self._cached_url = u''
    self._cached_page_content = b''
    self._download_url = download_url

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

      try:
        url_object = urllib2.urlopen(download_url)
      except urllib2.URLError as exception:
        logging.warning(
            u'Unable to download URL: {0:s} with error: {1:s}'.format(
                download_url, exception))
        return

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
      try:
        url_object = urllib2.urlopen(download_url)
      except urllib2.URLError as exception:
        logging.warning(
            u'Unable to download URL: {0:s} with error: {1:s}'.format(
                download_url, exception))
        return

      if url_object.code != 200:
        return

      self._cached_page_content = url_object.read()
      self._cached_url = download_url

    return self._cached_page_content


class ProjectDownloadHelper(DownloadHelper):
  """Class that helps in downloading a project."""

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

    filename = self.DownloadFile(download_url)

    # github archive package filenames can be:
    # {project version}.tar.gz
    # release-{project version}.tar.gz
    # v{project version}.tar.gz
    github_archive_filenames = [
        u'{0!s}.tar.gz'.format(project_version),
        u'release-{0!s}.tar.gz'.format(project_version),
        u'v{0!s}.tar.gz'.format(project_version)]

    if filename in github_archive_filenames:
      # The desired source package filename is:
      # {project name}-{project version}.tar.gz
      package_filename = u'{0:s}-{1:s}.tar.gz'.format(
          project_name, project_version)

      os.rename(filename, package_filename)
      filename = package_filename

    return filename

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


class GithubReleasesDownloadHelper(ProjectDownloadHelper):
  """Class that helps in downloading a project with GitHub releases."""

  _VERSION_EXPRESSIONS = [
      u'[0-9]+',
      u'[0-9]+[.][0-9]+',
      u'[0-9]+[.][0-9]+[.][0-9]+',
      u'release-[0-9]+[.][0-9]+[.][0-9]+',
      u'v[0-9]+[.][0-9]',
      u'v[0-9]+[.][0-9]+[.][0-9]+',
      u'[0-9]+[.][0-9]+[.][0-9]+[-][0-9]+']

  def __init__(self, download_url):
    """Initializes the download helper.

    Args:
      download_url: a string containing the download URL.
    """
    url_segments = download_url.split(u'/')

    super(GithubReleasesDownloadHelper, self).__init__(download_url)
    self.organization = url_segments[3]
    self.repository = url_segments[4]

  def GetLatestVersion(self, project_name):
    """Retrieves the latest version number for a given project name.

    Args:
      project_name: the name of the project.

    Returns:
      The latest version number or 0 on error.
    """
    # TODO: add support for URL arguments u'?after=release-2.2.0'
    download_url = u'https://github.com/{0:s}/{1:s}/releases'.format(
        self.organization, self.repository)

    page_content = self.DownloadPageContent(download_url)
    if not page_content:
      return 0

    # The format of the project download URL is:
    # /{organization}/{repository}/releases/download/{git tag}/
    # {project name}{status-}{version}.tar.gz
    # Note that the status is optional and will be: beta, alpha or experimental.
    # E.g. used by libyal.
    expression_string = (
        u'/{0:s}/{1:s}/releases/download/[^/]*/{2:s}-[a-z-]*({3:s})'
        u'[.]tar[.]gz').format(
            self.organization, self.repository, project_name,
            u'|'.join(self._VERSION_EXPRESSIONS))
    matches = re.findall(expression_string, page_content)

    if not matches:
      # The format of the project archive download URL is:
      # /{organization}/{repository}/archive/{version}.tar.gz
      expression_string = (
          u'/{0:s}/{1:s}/archive/({2:s})[.]tar[.]gz').format(
              self.organization, self.repository,
              u'|'.join(self._VERSION_EXPRESSIONS))
      matches = re.findall(expression_string, page_content)

    if not matches:
      # The format of the project archive download URL is:
      # /{organization}/{repository}/archive/{project name}-{version}.tar.gz
      expression_string = (
          u'/{0:s}/{1:s}/archive/{2:s}[-]({3:s})[.]tar[.]gz').format(
              self.organization, self.repository, project_name,
              u'|'.join(self._VERSION_EXPRESSIONS))
      matches = re.findall(expression_string, page_content)

    if not matches:
      return 0

    # Split the version string and convert every digit into an integer.
    # A string compare of both version strings will yield an incorrect result.
    comparable_matches = {}

    for match in matches:
      # Remove a leading 'release-'.
      if match.startswith(u'release-'):
        match = match[8:]
      # Remove a leading 'v'.
      elif match.startswith(u'v'):
        match = match[1:]

      # Some versions contain '-' as the release number separator for the split
      # we want this to be '.'.
      comparable_match = match.replace(u'-', u'.')

      comparable_match = map(int, comparable_match.split(u'.'))
      comparable_matches[match] = comparable_match

    # Find the latest version number and transform it back into a string.
    latest_match = [digit for digit in max(comparable_matches.values())]

    # Map the latest match value to its index within the dictionary.
    latest_match = comparable_matches.values().index(latest_match)

    # Return the original version string which is stored as the key in within
    # the dictionary.
    return comparable_matches.keys()[latest_match]

  def GetDownloadUrl(self, project_name, project_version):
    """Retrieves the download URL for a given project name and version.

    Args:
      project_name: the name of the project.
      project_version: the version of the project.

    Returns:
      The download URL of the project or None on error.
    """
    # TODO: add support for URL arguments u'?after=release-2.2.0'
    download_url = u'https://github.com/{0:s}/{1:s}/releases'.format(
        self.organization, self.repository)

    page_content = self.DownloadPageContent(download_url)
    if not page_content:
      return

    # The format of the project download URL is:
    # /{organization}/{repository}/releases/download/{git tag}/
    # {project name}{status-}{version}.tar.gz
    # Note that the status is optional and will be: beta, alpha or experimental.
    expression_string = (
        u'/{0:s}/{1:s}/releases/download/[^/]*/{2:s}-[a-z-]*{3!s}'
        u'[.]tar[.]gz').format(
            self.organization, self.repository, project_name, project_version)
    matches = re.findall(expression_string, page_content)

    if len(matches) != 1:
      # Try finding a match without the status in case the project provides
      # multiple versions with a different status.
      expression_string = (
          u'/{0:s}/{1:s}/releases/download/[^/]*/{2:s}-*{3!s}'
          u'[.]tar[.]gz').format(
              self.organization, self.repository, project_name,
              project_version)
      matches = re.findall(expression_string, page_content)

    if matches and len(matches) == 1:
      return u'https://github.com{0:s}'.format(matches[0])

    if matches and len(matches) != 1:
      return

    # The format of the project archive download URL is:
    # /{organization}/{repository}/archive/{version}.tar.gz
    expression_string = (
        u'/{0:s}/{1:s}/archive/{2!s}[.]tar[.]gz').format(
            self.organization, self.repository, project_version)
    matches = re.findall(expression_string, page_content)

    if matches and len(matches) == 1:
      return u'https://github.com{0:s}'.format(matches[0])

    if len(matches) != 1:
      # The format of the project archive download URL is:
      # /{organization}/{repository}/archive/release-{version}.tar.gz
      expression_string = (
          u'/{0:s}/{1:s}/archive/release-{2!s}[.]tar[.]gz').format(
              self.organization, self.repository, project_version)
      matches = re.findall(expression_string, page_content)

    if matches and len(matches) == 1:
      return u'https://github.com{0:s}'.format(matches[0])

    if len(matches) != 1:
      # The format of the project archive download URL is:
      # /{organization}/{repository}/archive/v{version}.tar.gz
      expression_string = (
          u'/{0:s}/{1:s}/archive/v{2!s}[.]tar[.]gz').format(
              self.organization, self.repository, project_version)
      matches = re.findall(expression_string, page_content)

    if matches and len(matches) == 1:
      return u'https://github.com{0:s}'.format(matches[0])

    if len(matches) != 1:
      # The format of the project archive download URL is:
      # /{organization}/{repository}/archive/{project name}-{version}.tar.gz
      expression_string = (
          u'/{0:s}/{1:s}/archive/{2:s}[-]{3!s}[.]tar[.]gz').format(
              self.organization, self.repository, project_name,
              project_version)
      matches = re.findall(expression_string, page_content)

    if matches and len(matches) == 1:
      return u'https://github.com{0:s}'.format(matches[0])

    return

  def GetProjectIdentifier(self, unused_project_name):
    """Retrieves the project identifier for a given project name.

    Args:
      project_name: the name of the project.

    Returns:
      The project identifier or None on error.
    """
    return u'com.github.{0:s}.{1:s}'.format(self.organization, self.repository)


# TODO: Merge with GithubReleasesDownloadHelper.
# pylint: disable=abstract-method
class LibyalGitHubDownloadHelper(ProjectDownloadHelper):
  """Class that helps in downloading a libyal GitHub project."""

  def __init__(self, download_url):
    """Initializes the download helper.

    Args:
      download_url: a string containing the download URL.
    """
    super(LibyalGitHubDownloadHelper, self).__init__(download_url)
    self._download_helper = None

  def GetProjectConfigurationSourcePackageUrl(self, project_name):
    """Retrieves the source package URL from the libyal project configuration.

    Args:
      project_name: the name of the project.

    Returns:
      The source package URL or None on error.
    """
    download_url = (
        u'https://raw.githubusercontent.com/libyal/{0:s}/master/'
        u'{0:s}.ini').format(project_name)

    page_content = self.DownloadPageContent(download_url)
    if not page_content:
      return

    config_parser = configparser.RawConfigParser()
    config_parser.readfp(io.BytesIO(page_content))

    return json.loads(config_parser.get(u'project', u'download_url'))

  def GetLatestVersion(self, project_name):
    """Retrieves the latest version number for a given project name.

    Args:
      project_name: the name of the project.

    Returns:
      The latest version number or 0 on error.
    """
    if not self._download_helper:
      download_url = self.GetProjectConfigurationSourcePackageUrl(project_name)
      if not download_url:
        return 0

      self._download_helper = GithubReleasesDownloadHelper(download_url)

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
      download_url = self.GetProjectConfigurationSourcePackageUrl(
          project_name)

      if not download_url:
        return 0

      self._download_helper = GithubReleasesDownloadHelper(download_url)

    return self._download_helper.GetDownloadUrl(project_name, project_version)


class PyPIDownloadHelper(ProjectDownloadHelper):
  """Class that helps in downloading a PyPI code project."""

  _VERSION_EXPRESSIONS = [
      u'[0-9]+',
      u'[0-9]+[.][0-9]+',
      u'[0-9]+[.][0-9]+a[0-9]',
      u'[0-9]+[.][0-9]+[.][0-9]+',
      u'[0-9]+[.][0-9]+rc[0-9]+',
      u'[0-9]+[.][0-9]+[.][0-9]+[.][0-9]+',
      u'[0-9]+[.][0-9]+[.][0-9]+rc[0-9]+']

  def GetLatestVersion(self, project_name):
    """Retrieves the latest version number for a given project name.

    Args:
      project_name: the name of the project.

    Returns:
      The a string containing the latest version number or None on error.
    """
    download_url = u'https://pypi.python.org/pypi/{0:s}'.format(project_name)

    page_content = self.DownloadPageContent(download_url)
    if not page_content:
      return

    expression_string = u'<h1>Index of Packages</h1>'
    matches = re.findall(expression_string, page_content)

    if matches:
      # Some PyPI pages are indexes of packages which contain links to
      # versioned sub pages in the form:
      # /pypi/{project name}/{version}
      expression_string = (
          u'<a href="/pypi/{0:s}/({1:s})">').format(
              project_name, u'|'.join(self._VERSION_EXPRESSIONS))
      matches = re.findall(expression_string, page_content)

    else:
      # The format of the project download URL is:
      # https://pypi.python.org/packages/.*/{project name}-{version}.tar.gz
      expression_string = (
          u'https://pypi.python.org/packages/.*/'
          u'{0:s}-({1:s})[.]tar[.]gz').format(
              project_name, u'|'.join(self._VERSION_EXPRESSIONS))
      matches = re.findall(expression_string, page_content)

    if not matches:
      return

    # The letter a is used in some versions to denote an alpha release.
    # The suffix rc# is used in some versions to denote a release candidate.
    numeric_matches = [match for match in matches if match.isdigit()]

    # If there are stable releases prefer those:
    if numeric_matches:
      # Split the version string and convert every digit into an integer.
      # A string compare of both version strings will yield an incorrect result.
      numeric_matches = [
          map(int, match.split(u'.')) for match in numeric_matches]

      # Find the latest version number and transform it back into a string.
      return u'.'.join([
          u'{0:d}'.format(digit) for digit in max(numeric_matches)])

    return sorted(matches)[-1]

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


class SourceForgeDownloadHelper(ProjectDownloadHelper):
  """Class that helps in downloading a Source Forge project."""

  def GetLatestVersion(self, project_name):
    """Retrieves the latest version number for a given project name.

    Args:
      project_name: the name of the project.

    Returns:
      The a string containing the latest version number or 0 on error.
    """
    if project_name == u'zlib':
      main_project_name = u'libpng'
    else:
      main_project_name = project_name

    # TODO: make this more robust to detect different naming schemes.
    download_url = (
        u'https://sourceforge.net/projects/{0:s}/files/{1:s}/').format(
            main_project_name, project_name)

    page_content = self.DownloadPageContent(download_url)
    if not page_content:
      return 0

    if project_name == u'pyparsing':
      # The format of the project download URL is:
      # /projects/{project name}/files/{project name}/{project name}-{version}/
      expression_string = (
          u'<a href="/projects/{0:s}/files/{1:s}/'
          u'{1:s}-([0-9]+[.][0-9]+[.][0-9]+)/"').format(
              main_project_name, project_name)
      matches = re.findall(expression_string, page_content)

    elif project_name == u'pywin32':
      # The format of the project download URL is:
      # /projects/{project name}/files/{project name}/Build%20{version}/
      expression_string = (
          u'<a href="/projects/{0:s}/files/{1:s}/Build%20([0-9]+)/"').format(
              main_project_name, project_name)
      matches = re.findall(expression_string, page_content)

    elif project_name in [u'sleuthkit', u'zlib']:
      # The format of the project download URL is:
      # /projects/{project name}/files/{project name}/{version}/
      expression_string = (
          u'<a href="/projects/{0:s}/files/{1:s}/'
          u'([0-9]+[.][0-9]+[.][0-9]+)/"').format(
              main_project_name, project_name)
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
    if project_name == u'zlib':
      main_project_name = u'libpng'
    else:
      main_project_name = project_name

    # TODO: make this more robust to detect different naming schemes.
    download_url = (
        u'https://sourceforge.net/projects/{0:s}/files/{1:s}/').format(
            main_project_name, project_name)

    page_content = self.DownloadPageContent(download_url)
    if not page_content:
      return

    download_url = None
    if project_name == u'pyparsing':
      # The format of the project download URL is:
      # /projects/{project name}/files/{project name}/{project name}-{version}/
      expression_string = (
          u'<a href="/projects/{0:s}/files/{1:s}/{1:s}-({2:s})/"').format(
              main_project_name, project_name, project_version)
      matches = re.findall(expression_string, page_content)

      if matches:
        download_url = (
            u'https://downloads.sourceforge.net/project/{0:s}/{1:s}/{1:s}-{2:s}'
            u'/{1:s}-{2:s}.tar.gz').format(
                main_project_name, project_name, project_version)

    elif project_name == u'pywin32':
      # The format of the project download URL is:
      # /projects/{project name}/files/{project name}/Build%20{version}/
      expression_string = (
          u'<a href="/projects/{0:s}/files/{1:s}/Build%20({2:s})/"').format(
              main_project_name, project_name, project_version)
      matches = re.findall(expression_string, page_content)

      if matches:
        download_url = (
            u'https://downloads.sourceforge.net/project/{0:s}/{1:s}'
            u'/Build%20{2:s}/{1:s}-{2:s}.zip').format(
                main_project_name, project_name, project_version)

    elif project_name in [u'sleuthkit', u'zlib']:
      # The format of the project download URL is:
      # /projects/{project name}/files/{project name}/{version}/
      expression_string = (
          u'<a href="/projects/{0:s}/files/{1:s}/({2:s})/"').format(
              main_project_name, project_name, project_version)
      matches = re.findall(expression_string, page_content)

      if matches:
        download_url = (
            u'https://downloads.sourceforge.net/project/{0:s}/{1:s}/{2:s}'
            u'/{1:s}-{2:s}.tar.gz').format(
                main_project_name, project_name, project_version)

    return download_url

  def GetProjectIdentifier(self, project_name):
    """Retrieves the project identifier for a given project name.

    Args:
      project_name: the name of the project.

    Returns:
      The project identifier or None on error.
    """
    return u'net.sourceforge.projects.{0:s}'.format(project_name)


class DownloadHelperFactory(object):
  """Factory class for download helpers."""

  @classmethod
  def NewDownloadHelper(cls, download_url):
    """Creates a new download helper object.

    Args:
      download_url: a string containing the download URL.

    Returns:
      A download helper object (instance of DownloadHelper) or None.
    """
    if download_url.endswith(u'/'):
      download_url = download_url[:-1]

    # Unify http:// and https:// URLs for the download helper check.
    if download_url.startswith(u'https://'):
      download_url = u'http://{0:s}'.format(download_url[8:])

    # Remove URL arguments.
    download_url, _, _ = download_url.partition(u'?')

    if download_url.startswith(u'http://pypi.python.org/pypi/'):
      download_helper_class = PyPIDownloadHelper

    elif (download_url.startswith(u'http://sourceforge.net/projects/') and
          download_url.endswith(u'/files')):
      download_helper_class = SourceForgeDownloadHelper

    # TODO: make this a more generic github download helper.
    elif (download_url.startswith(u'http://github.com/libyal/') or
          download_url.startswith(u'http://googledrive.com/host/')):
      download_helper_class = LibyalGitHubDownloadHelper

    elif (download_url.startswith(u'http://github.com/') and
          download_url.endswith(u'/releases')):
      download_helper_class = GithubReleasesDownloadHelper

    else:
      download_helper_class = None

    if not download_helper_class:
      return

    return download_helper_class(download_url)
