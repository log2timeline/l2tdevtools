# -*- coding: utf-8 -*-
"""Download helper object implementations."""

import re

# pylint: disable=wrong-import-position
import pkg_resources

from l2tdevtools.download_helpers import project


class PyPIDownloadHelper(project.ProjectDownloadHelper):
  """Helps in downloading a PyPI code project."""

  def __init__(self, download_url, source_name=None):
    """Initializes the download helper.

    Args:
      download_url (str): download URL.
      source_name (Optional[str]): PyPI source pacakge name, where None
          indicates the source package name is the same as the PyPI project
          name.

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
    self._source_name = source_name or self._project_name

  def _GetAvailableVersions(self, version_strings):
    """Determines the available versions from version string matched.

    This function will split the version string and convert every digit into
    an integer. These lists of integers allow us to reliable compare versions.
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

      # Convert the result of map() into a list for Python 3.
      comparable_version = version_object.base_version.split('.')
      comparable_version = list(map(int, comparable_version))
      comparable_version.insert(0, epoch)

      # Add the epoch to the version string for comparison.
      available_versions[version_string] = comparable_version

    return available_versions

  # pylint: disable=unused-argument
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

    download_url = 'https://pypi.org/pypi/{0:s}/json'.format(self._project_name)

    page_content = self.DownloadPageContent(download_url)
    if not page_content:
      return None

    expression_string = (
        r'"https://files.pythonhosted.org/packages/.*/.*/.*/'
        r'{0:s}-([\d\.\!]*(post\d+)?)\.(tar\.bz2|tar\.gz|zip)"').format(
            self._source_name)

    matches = re.findall(expression_string, page_content, flags=re.IGNORECASE)
    if not matches:
      return None

    available_versions = self._GetAvailableVersions([
        match[0] for match in matches])
    return self._GetLatestVersion(
        earliest_version, latest_version, available_versions, with_epoch=True)

  def GetDownloadURL(self, project_name, project_version):
    """Retrieves the download URL for a given project name and version.

    Args:
      project_name (str): name of the project.
      project_version (str): version of the project.

    Returns:
      str: download URL of the project or None if not available.
    """
    download_url = 'https://pypi.org/pypi/{0:s}/json'.format(self._project_name)

    page_content = self.DownloadPageContent(download_url)
    if not page_content:
      return None

    # The format of the project download URL is:
    # https://files.pythonhosted.org/packages/[0-9a-f]*/[0-9a-f]*/[0-9a-f]*/
    #     {project name}-{version}.{extension}
    expression_string = (
        '(https://files.pythonhosted.org/packages/[0-9a-f]*/[0-9a-f]*/'
        '[0-9a-f]*/{0:s}-{1!s}[.](tar[.]bz2|tar[.]gz|zip))').format(
            self._source_name, project_version)
    matches = re.findall(expression_string, page_content, flags=re.IGNORECASE)

    if not matches:
      return None

    return matches[0][0]

  def GetProjectIdentifier(self):
    """Retrieves the project identifier for a given project name.

    Returns:
      str: project identifier.
    """
    return 'org.pypi.{0:s}'.format(self._project_name)
