# -*- coding: utf-8 -*-
"""Download helper object implementations."""

from l2tdevtools.download_helpers import github
from l2tdevtools.download_helpers import pypi
from l2tdevtools.download_helpers import sourceforge


class DownloadHelperFactory(object):
  """Factory class for download helpers."""

  @classmethod
  def NewDownloadHelper(cls, project_definition):
    """Creates a new download helper.

    Args:
      project_definition (ProjectDefinition): project definition.

    Returns:
      DownloadHelper: download helper.

    Raises:
      ValueError: if no corresponding helper could be found for the download
          URL.
    """
    download_url = project_definition.download_url

    if download_url.endswith('/'):
      download_url = download_url[:-1]

    # Unify http:// and https:// URLs for the download helper check.
    if download_url.startswith('https://'):
      download_url = 'http://{0:s}'.format(download_url[8:])

    # Remove URL arguments.
    download_url, _, _ = download_url.partition('?')

    if download_url.startswith('http://pypi.org/project/'):
      return pypi.PyPIDownloadHelper(
          download_url, source_name=project_definition.pypi_source_name)

    if (download_url.startswith('http://sourceforge.net/projects/') and
        download_url.endswith('/files')):
      return sourceforge.SourceForgeDownloadHelper(download_url)

    if (download_url.startswith('http://github.com/') and
        download_url.endswith('/releases')):
      return github.GitHubReleasesDownloadHelper(download_url)

    raise ValueError('Unsupported download URL: {0:s}.'.format(
        project_definition.download_url))
