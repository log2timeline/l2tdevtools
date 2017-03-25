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

import pkg_resources


class DownloadHelper(object):
  """Helps in downloading files and web content."""

  def __init__(self, download_url):
    """Initializes the download helper.

    Args:
      download_url (str): download URL.
    """
    super(DownloadHelper, self).__init__()
    self._cached_url = u''
    self._cached_page_content = b''
    self._download_url = download_url

  def DownloadFile(self, download_url):
    """Downloads a file from the URL and returns the filename.

    The filename is extracted from the last part of the URL.

    Args:
      download_url (str): URL where to download the file.

    Returns:
      str: filename if successful also if the file was already downloaded
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
      download_url (str): URL where to download the page content.

    Returns:
      str: page content if successful, None otherwise.
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
          or None on error.
    """
    download_url = self.GetDownloadURL(project_name, project_version)
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


class GitHubReleasesDownloadHelper(ProjectDownloadHelper):
  """Helps in downloading a project with GitHub releases."""

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
      download_url (str): download URL.

    Raises:
      ValueError: if download URL is not supported.
    """
    url_segments = download_url.split(u'/')
    if len(url_segments) < 5 or url_segments[2] != u'github.com':
      raise ValueError(u'Unsupported download URL.')

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
      str: latest version number or None on error.
    """
    if version_definition:
      earliest_version = version_definition.GetEarliestVersion()
      if earliest_version and earliest_version[0] == u'==':
        return u'.'.join(earliest_version[1:])

    download_url = u'https://github.com/{0:s}/{1:s}/releases'.format(
        self._organization, self._repository)

    # TODO: add support for URL arguments u'?after=release-2.2.0'
    # if earliest_version:
    #   download_url = u'{0:s}?after={1:s}'.format(
    #       download_url, earliest_version)

    page_content = self.DownloadPageContent(download_url)
    if not page_content:
      return

    # The format of the project download URL is:
    # /{organization}/{repository}/releases/download/{git tag}/
    # {project name}{status-}{version}.tar.gz
    # Note that the status is optional and will be: beta, alpha or experimental.
    # E.g. used by libyal.
    expression_string = (
        u'/{0:s}/{1:s}/releases/download/[^/]*/{2:s}-[a-z-]*({3:s})'
        u'[.]tar[.]gz[^.]').format(
            self._organization, self._repository, project_name,
            u'|'.join(self._VERSION_EXPRESSIONS))
    matches = re.findall(expression_string, page_content)

    if not matches:
      # The format of the project archive download URL is:
      # /{organization}/{repository}/archive/{version}.tar.gz
      expression_string = (
          u'/{0:s}/{1:s}/archive/({2:s})[.]tar[.]gz[^.]').format(
              self._organization, self._repository,
              u'|'.join(self._VERSION_EXPRESSIONS))
      matches = re.findall(expression_string, page_content)

    if not matches:
      # The format of the project archive download URL is:
      # /{organization}/{repository}/archive/{project name}-{version}.tar.gz
      expression_string = (
          u'/{0:s}/{1:s}/archive/{2:s}[-]({3:s})[.]tar[.]gz[^.]').format(
              self._organization, self._repository, project_name,
              u'|'.join(self._VERSION_EXPRESSIONS))
      matches = re.findall(expression_string, page_content)

      # TODO: this check will fail if the case in the URL is different.
      # Make checks case insenstive.

    if not matches:
      return

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

  def GetDownloadURL(self, project_name, project_version):
    """Retrieves the download URL for a given project name and version.

    Args:
      project_name (str): name of the project.
      project_version (str): version of the project.

    Returns:
      str: download URL of the project or None on error.
    """
    # TODO: add support for URL arguments u'?after=release-2.2.0'
    download_url = u'https://github.com/{0:s}/{1:s}/releases'.format(
        self._organization, self._repository)

    page_content = self.DownloadPageContent(download_url)
    if not page_content:
      return

    # The format of the project download URL is:
    # /{organization}/{repository}/releases/download/{git tag}/
    # {project name}{status-}{version}.tar.gz
    # Note that the status is optional and will be: beta, alpha or experimental.
    expression_string = (
        u'/{0:s}/{1:s}/releases/download/[^/]*/{2:s}-[a-z-]*{3!s}'
        u'[.]tar[.]gz[^.]').format(
            self._organization, self._repository, project_name, project_version)
    matches = re.findall(expression_string, page_content)

    if len(matches) != 1:
      # Try finding a match without the status in case the project provides
      # multiple versions with a different status.
      expression_string = (
          u'/{0:s}/{1:s}/releases/download/[^/]*/{2:s}-*{3!s}'
          u'[.]tar[.]gz[^.]').format(
              self._organization, self._repository, project_name,
              project_version)
      matches = re.findall(expression_string, page_content)

    if matches and len(matches) == 1:
      return u'https://github.com{0:s}'.format(matches[0][:-1])

    if matches and len(matches) != 1:
      return

    # The format of the project archive download URL is:
    # /{organization}/{repository}/archive/{version}.tar.gz
    expression_string = (
        u'/{0:s}/{1:s}/archive/{2!s}[.]tar[.]gz[^.]').format(
            self._organization, self._repository, project_version)
    matches = re.findall(expression_string, page_content)

    if matches and len(matches) == 1:
      return u'https://github.com{0:s}'.format(matches[0][:-1])

    if len(matches) != 1:
      # The format of the project archive download URL is:
      # /{organization}/{repository}/archive/release-{version}.tar.gz
      expression_string = (
          u'/{0:s}/{1:s}/archive/release-{2!s}[.]tar[.]gz[^.]').format(
              self._organization, self._repository, project_version)
      matches = re.findall(expression_string, page_content)

    if matches and len(matches) == 1:
      return u'https://github.com{0:s}'.format(matches[0][:-1])

    if len(matches) != 1:
      # The format of the project archive download URL is:
      # /{organization}/{repository}/archive/v{version}.tar.gz
      expression_string = (
          u'/{0:s}/{1:s}/archive/v{2!s}[.]tar[.]gz[^.]').format(
              self._organization, self._repository, project_version)
      matches = re.findall(expression_string, page_content)

    if matches and len(matches) == 1:
      return u'https://github.com{0:s}'.format(matches[0][:-1])

    if len(matches) != 1:
      # The format of the project archive download URL is:
      # /{organization}/{repository}/archive/{project name}-{version}.tar.gz
      expression_string = (
          u'/{0:s}/{1:s}/archive/{2:s}[-]{3!s}[.]tar[.]gz[^.]').format(
              self._organization, self._repository, project_name,
              project_version)
      matches = re.findall(expression_string, page_content)

    if matches and len(matches) == 1:
      return u'https://github.com{0:s}'.format(matches[0][:-1])

    return

  def GetProjectIdentifier(self):
    """Retrieves the project identifier for a given project name.

    Returns:
      str: project identifier.
    """
    return u'com.github.{0:s}.{1:s}'.format(
        self._organization, self._repository)


# TODO: Merge with GitHubReleasesDownloadHelper.
# pylint: disable=abstract-method
class LibyalGitHubDownloadHelper(ProjectDownloadHelper):
  """Helps in downloading a libyal GitHub project."""

  def __init__(self, download_url):
    """Initializes the download helper.

    Args:
      download_url (str): download URL.
    """
    super(LibyalGitHubDownloadHelper, self).__init__(download_url)
    self._download_helper = None

  def GetProjectConfigurationSourcePackageURL(self, project_name):
    """Retrieves the source package URL from the libyal project configuration.

    Args:
      project_name (str): name of the project.

    Returns:
      str: source package URL or None on error.
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

  def GetLatestVersion(self, project_name, version_definition):
    """Retrieves the latest version number for a given project name.

    Args:
      project_name (str): name of the project.
      version_definition (ProjectVersionDefinition): project version definition
          or None.

    Returns:
      str: latest version number or None on error.
    """
    if not self._download_helper:
      download_url = self.GetProjectConfigurationSourcePackageURL(project_name)
      if not download_url:
        return

      self._download_helper = GitHubReleasesDownloadHelper(download_url)

    return self._download_helper.GetLatestVersion(
        project_name, version_definition)

  def GetDownloadURL(self, project_name, project_version):
    """Retrieves the download URL for a given project name and version.

    Args:
      project_name (str): name of the project.
      project_version (str): version of the project.

    Returns:
      str: download URL of the project or None on error.
    """
    if not self._download_helper:
      download_url = self.GetProjectConfigurationSourcePackageURL(
          project_name)

      if not download_url:
        return 0

      self._download_helper = GitHubReleasesDownloadHelper(download_url)

    return self._download_helper.GetDownloadURL(project_name, project_version)


class PyPIDownloadHelper(ProjectDownloadHelper):
  """Helps in downloading a PyPI code project."""

  def __init__(self, download_url):
    """Initializes the download helper.

    Args:
      download_url (str): download URL.

    Raises:
      ValueError: if download URL is not supported.
    """
    url_segments = download_url.split(u'/')
    if (len(url_segments) < 5 or url_segments[2] != u'pypi.python.org' or
        url_segments[3] != u'pypi'):
      raise ValueError(u'Unsupported download URL.')

    super(PyPIDownloadHelper, self).__init__(download_url)
    self._project_name = url_segments[4]

  def GetLatestVersion(self, unused_project_name, version_definition):
    """Retrieves the latest version number for a given project name.

    Args:
      project_name (str): name of the project.
      version_definition (ProjectVersionDefinition): project version definition
          or None.

    Returns:
      str: latest version number or None on error.
    """
    if version_definition:
      earliest_version = version_definition.GetEarliestVersion()
      if earliest_version and earliest_version[0] == u'==':
        return u'.'.join(earliest_version[1:])

    download_url = u'https://pypi.python.org/simple/{0:s}'.format(
        self._project_name)

    page_content = self.DownloadPageContent(download_url)
    if not page_content:
      return

    versions = {}
    expression_string = (
        r'../../packages/.*/{0:s}-(?P<version>[\d\.\!]*)'
        r'\.(tar\.bz2|tar\.gz|zip)#').format(self._project_name)
    for match in re.finditer(expression_string, page_content):
      version_string = match.group(u'version')
      if version_string:
        # We need to support PEP440 epoch versioning, which only newly versions
        # of setuptools support. So this is a bit of hack to handle epochs
        # but still use setuptools to handle most of the version matching.
        epoch, _, epoch_version_string = version_string.partition(u'!')
        if not epoch_version_string:
          # Per PEP440, if there's no epoch specified, the epoch is 0.
          epoch_version_string = epoch
          epoch = 0
        else:
          epoch = int(epoch, 10)
        version = list(pkg_resources.parse_version(epoch_version_string))
        # Add the epoch to the version string for comparison.
        version.insert(0, epoch)
        version_tuple = (tuple(version), version_string)
        versions[version_tuple] = version_string

    latest_version = max(versions.keys())
    if latest_version:
      # Return the original string that defined the version
      return versions[latest_version]

  def GetDownloadURL(self, unused_project_name, project_version):
    """Retrieves the download URL for a given project name and version.

    Args:
      project_name (str): name of the project.
      project_version (str): version of the project.

    Returns:
      str: download URL of the project or None on error.
    """
    download_url = (
        u'https://pypi.python.org/pypi/{0:s}/{1!s}').format(
            self._project_name, project_version)

    page_content = self.DownloadPageContent(download_url)
    if not page_content:
      return

    # The format of the project download URL is:
    # https://pypi.python.org/packages/.*/{project name}-{version}.{extension}
    expression_string = (
        u'(https://pypi.python.org/packages/.*/'
        u'{0:s}-{1!s}[.](tar[.]bz2|tar[.]gz|zip))').format(
            self._project_name, project_version)
    matches = re.findall(expression_string, page_content)

    if matches:
      return matches[0][0]

    return (
        u'https://pypi.python.org/packages/source/{0:s}/{1:s}/'
        u'{1:s}-{2:s}.tar.gz').format(
            self._project_name[0], self._project_name, project_version)

  def GetProjectIdentifier(self):
    """Retrieves the project identifier for a given project name.

    Returns:
      str: project identifier.
    """
    return u'org.python.pypi.{0:s}'.format(self._project_name)


class SourceForgeDownloadHelper(ProjectDownloadHelper):
  """Helps in downloading a Source Forge project."""

  def __init__(self, download_url):
    """Initializes the download helper.

    Args:
      download_url (str): download URL.

    Raises:
      ValueError: if download URL is not supported.
    """
    url_segments = download_url.split(u'/')
    if (len(url_segments) < 5 or url_segments[2] != u'sourceforge.net' or
        url_segments[3] != u'projects' or url_segments[5] != u'files'):
      raise ValueError(u'Unsupported download URL.')

    super(SourceForgeDownloadHelper, self).__init__(download_url)
    self._project_name = url_segments[4]

  def GetLatestVersion(self, unused_project_name, version_definition):
    """Retrieves the latest version number for a given project name.

    Args:
      project_name (str): name of the project.
      version_definition (ProjectVersionDefinition): project version definition
          or None.

    Returns:
      str: latest version number or None on error.
    """
    if version_definition:
      earliest_version = version_definition.GetEarliestVersion()
      if earliest_version and earliest_version[0] == u'==':
        return u'.'.join(earliest_version[1:])

    # TODO: make this more robust to detect different naming schemes.
    download_url = (
        u'https://sourceforge.net/projects/{0:s}/files/{0:s}/').format(
            self._project_name)

    page_content = self.DownloadPageContent(download_url)
    if not page_content:
      return

    if self._project_name == u'pyparsing':
      # The format of the project download URL is:
      # /projects/{project name}/files/{project name}/{project name}-{version}/
      expression_string = (
          u'<a href="/projects/{0:s}/files/{0:s}/'
          u'{0:s}-([0-9]+[.][0-9]+[.][0-9]+)/"').format(
              self._project_name)
      matches = re.findall(expression_string, page_content)

    elif self._project_name == u'pywin32':
      # The format of the project download URL is:
      # /projects/{project name}/files/{project name}/Build%20{version}/
      expression_string = (
          u'<a href="/projects/{0:s}/files/{0:s}/Build%20([0-9]+)/"').format(
              self._project_name)
      matches = re.findall(expression_string, page_content)

    if not matches:
      return

    numeric_matches = [u''.join(match.split(u'.')) for match in matches]
    return matches[numeric_matches.index(max(numeric_matches))]

  def GetDownloadURL(self, unused_project_name, project_version):
    """Retrieves the download URL for a given project name and version.

    Args:
      project_name (str): name of the project.
      project_version (str): version of the project.

    Returns:
      The download URL of the project or None on error.
    """
    # TODO: make this more robust to detect different naming schemes.
    download_url = (
        u'https://sourceforge.net/projects/{0:s}/files/{0:s}/').format(
            self._project_name)

    page_content = self.DownloadPageContent(download_url)
    if not page_content:
      return

    download_url = None
    if self._project_name == u'pyparsing':
      # The format of the project download URL is:
      # /projects/{project name}/files/{project name}/{project name}-{version}/
      expression_string = (
          u'<a href="/projects/{0:s}/files/{0:s}/{0:s}-({1:s})/"').format(
              self._project_name, project_version)
      matches = re.findall(expression_string, page_content)

      if matches:
        download_url = (
            u'https://downloads.sourceforge.net/project/{0:s}/{0:s}/{0:s}-{1:s}'
            u'/{0:s}-{1:s}.tar.gz').format(
                self._project_name, project_version)

    elif self._project_name == u'pywin32':
      # The format of the project download URL is:
      # /projects/{project name}/files/{project name}/Build%20{version}/
      expression_string = (
          u'<a href="/projects/{0:s}/files/{0:s}/Build%20({1:s})/"').format(
              self._project_name, project_version)
      matches = re.findall(expression_string, page_content)

      if matches:
        download_url = (
            u'https://downloads.sourceforge.net/project/{0:s}/{0:s}'
            u'/Build%20{1:s}/{0:s}-{1:s}.zip').format(
                self._project_name, project_version)

    return download_url

  def GetProjectIdentifier(self):
    """Retrieves the project identifier for a given project name.

    Returns:
      str: project identifier.
    """
    return u'net.sourceforge.projects.{0:s}'.format(self._project_name)


class ZlibDownloadHelper(ProjectDownloadHelper):
  """Helps in downloading the zlib project."""

  def __init__(self, download_url):
    """Initializes the download helper.

    Args:
      download_url (str): download URL.

    Raises:
      ValueError: if download URL is not supported.
    """
    url_segments = download_url.split(u'/')
    if len(url_segments) < 3 or url_segments[2] != u'www.zlib.net':
      raise ValueError(u'Unsupported download URL.')

    super(ZlibDownloadHelper, self).__init__(download_url)
    self._project_name = u'zlib'

  def GetLatestVersion(self, unused_project_name, unused_version_definition):
    """Retrieves the latest version number for a given project name.

    Args:
      project_name (str): name of the project.
      version_definition (ProjectVersionDefinition): project version definition
          or None.

    Returns:
      str: latest version number or None on error.
    """
    download_url = u'http://www.zlib.net'

    page_content = self.DownloadPageContent(download_url)
    if not page_content:
      return

    # The format of the project download URL is:
    # http://zlib.net/{project name}-{version}.tar.gz
    expression_string = (
        u'<A HREF="{0:s}-([0-9]+.[0-9]+.[0-9]+).tar.gz"').format(
            self._project_name)
    matches = re.findall(expression_string, page_content)

    if not matches:
      return

    numeric_matches = [u''.join(match.split(u'.')) for match in matches]
    return matches[numeric_matches.index(max(numeric_matches))]

  def GetDownloadURL(self, unused_project_name, project_version):
    """Retrieves the download URL for a given project name and version.

    Args:
      project_name (str): name of the project.
      project_version (str): version of the project.

    Returns:
      The download URL of the project or None on error.
    """
    # The format of the project download URL is:
    # http://zlib.net/{project name}-{version}.tar.gz
    return u'http://zlib.net/{0:s}-{1:s}.tar.gz'.format(
        self._project_name, project_version)

  def GetProjectIdentifier(self):
    """Retrieves the project identifier for a given project name.

    Returns:
      str: project identifier.
    """
    return u'net.zlib.{0:s}'.format(self._project_name)


class DownloadHelperFactory(object):
  """Factory class for download helpers."""

  @classmethod
  def NewDownloadHelper(cls, download_url):
    """Creates a new download helper.

    Args:
      download_url (str): download URL.

    Returns:
      DownloadHelper: download helper or None.
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
    elif (u'dtfabric' not in download_url and (
        download_url.startswith(u'http://github.com/libyal/') or
        download_url.startswith(u'http://googledrive.com/host/'))):
      download_helper_class = LibyalGitHubDownloadHelper

    elif (download_url.startswith(u'http://github.com/') and
          download_url.endswith(u'/releases')):
      download_helper_class = GitHubReleasesDownloadHelper

    else:
      download_helper_class = None

    if not download_helper_class:
      return

    return download_helper_class(download_url)
