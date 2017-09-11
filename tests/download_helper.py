#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the download helper object implementations."""

from __future__ import unicode_literals

import os
import shutil
import tempfile
import unittest

from l2tdevtools import download_helper


class TempDirectory(object):
  """A self cleaning temporary directory."""

  def __init__(self):
    """Initializes the temporary directory."""
    super(TempDirectory, self).__init__()
    self.name = ''

  def __enter__(self):
    """Make this work with the 'with' statement."""
    self.name = tempfile.mkdtemp()
    return self.name

  def __exit__(self, unused_type, unused_value, unused_traceback):
    """Make this work with the 'with' statement."""
    shutil.rmtree(self.name, True)


class DownloadHelperTest(unittest.TestCase):
  """Tests for the download helper."""

  _FILENAME = 'LICENSE'

  def setUp(self):
    """Sets up a test case."""
    self._download_url = (
        'https://raw.githubusercontent.com/log2timeline/l2tdevtools/master/'
        '{0:s}').format(self._FILENAME)

  def testDownloadPageContent(self):
    """Tests the DownloadPageContent functions."""
    download_helper_object = download_helper.DownloadHelper('')

    page_content = download_helper_object.DownloadPageContent(
        self._download_url)

    expected_page_content = b''
    with open(self._FILENAME, 'rb') as file_object:
      expected_page_content = file_object.read()

    self.assertEqual(page_content, expected_page_content)

  def testDownloadFile(self):
    """Tests the DownloadFile functions."""
    download_helper_object = download_helper.DownloadHelper(
        self._download_url)

    current_working_directory = os.getcwd()

    page_content = b''
    with TempDirectory() as temporary_directory:
      os.chdir(temporary_directory)
      filename = download_helper_object.DownloadFile(self._download_url)

      with open(filename, 'rb') as file_object:
        page_content = file_object.read()

    os.chdir(current_working_directory)

    expected_page_content = b''
    with open(self._FILENAME, 'rb') as file_object:
      expected_page_content = file_object.read()

    self.assertEqual(page_content, expected_page_content)


class DocoptGitHubReleasesDownloadHelperTest(unittest.TestCase):
  """Tests for the docopt github releases download helper."""

  _DOWNLOAD_URL = 'https://github.com/docopt/docopt/releases'

  _PROJECT_ORGANIZATION = 'docopt'
  _PROJECT_NAME = 'docopt'
  _PROJECT_VERSION = '0.6.2'

  def testGetLatestVersion(self):
    """Tests the GetLatestVersion functions."""
    download_helper_object = download_helper.GitHubReleasesDownloadHelper(
        self._DOWNLOAD_URL)

    latest_version = download_helper_object.GetLatestVersion(
        self._PROJECT_NAME, None)

    self.assertEqual(latest_version, self._PROJECT_VERSION)

  def testGetDownloadURL(self):
    """Tests the GetDownloadURL functions."""
    download_helper_object = download_helper.GitHubReleasesDownloadHelper(
        self._DOWNLOAD_URL)

    download_url = download_helper_object.GetDownloadURL(
        self._PROJECT_NAME, self._PROJECT_VERSION)

    expected_download_url = (
        'https://github.com/{0:s}/{1:s}/archive/{2:s}.tar.gz').format(
            self._PROJECT_ORGANIZATION, self._PROJECT_NAME,
            self._PROJECT_VERSION)

    self.assertEqual(download_url, expected_download_url)

  def testGetProjectIdentifier(self):
    """Tests the GetProjectIdentifier functions."""
    download_helper_object = download_helper.GitHubReleasesDownloadHelper(
        self._DOWNLOAD_URL)

    project_identifier = download_helper_object.GetProjectIdentifier()

    expected_project_identifier = 'com.github.{0:s}.{1:s}'.format(
        self._PROJECT_ORGANIZATION, self._PROJECT_NAME)

    self.assertEqual(project_identifier, expected_project_identifier)


class LibyalGitHubReleasesDownloadHelperTest(unittest.TestCase):
  """Tests for the libyal github releases download helper."""

  _DOWNLOAD_URL = 'https://github.com/libyal/libevt/releases'

  _PROJECT_ORGANIZATION = 'libyal'
  _PROJECT_NAME = 'libevt'
  _PROJECT_STATUS = 'alpha'
  _PROJECT_VERSION = '20170120'

  def testGetLatestVersion(self):
    """Tests the GetLatestVersion functions."""
    download_helper_object = download_helper.GitHubReleasesDownloadHelper(
        self._DOWNLOAD_URL)

    latest_version = download_helper_object.GetLatestVersion(
        self._PROJECT_NAME, None)

    self.assertEqual(latest_version, self._PROJECT_VERSION)

  def testGetDownloadURL(self):
    """Tests the GetDownloadURL functions."""
    download_helper_object = download_helper.GitHubReleasesDownloadHelper(
        self._DOWNLOAD_URL)

    download_url = download_helper_object.GetDownloadURL(
        self._PROJECT_NAME, self._PROJECT_VERSION)

    expected_download_url = (
        'https://github.com/{0:s}/{1:s}/releases/download/{3:s}/'
        '{1:s}-{2:s}-{3:s}.tar.gz').format(
            self._PROJECT_ORGANIZATION, self._PROJECT_NAME,
            self._PROJECT_STATUS, self._PROJECT_VERSION)

    self.assertEqual(download_url, expected_download_url)

  def testGetProjectIdentifier(self):
    """Tests the GetProjectIdentifier functions."""
    download_helper_object = download_helper.GitHubReleasesDownloadHelper(
        self._DOWNLOAD_URL)

    project_identifier = download_helper_object.GetProjectIdentifier()

    expected_project_identifier = 'com.github.{0:s}.{1:s}'.format(
        self._PROJECT_ORGANIZATION, self._PROJECT_NAME)

    self.assertEqual(project_identifier, expected_project_identifier)


class Log2TimelineGitHubReleasesDownloadHelperTest(unittest.TestCase):
  """Tests for the log2timeline GitHub releases download helper."""

  _DOWNLOAD_URL = 'https://github.com/log2timeline/dfvfs/releases'

  _PROJECT_ORGANIZATION = 'log2timeline'
  _PROJECT_NAME = 'dfvfs'
  # Hard-coded version to check parsing of GitHub page.
  _PROJECT_VERSION = '20170723'

  def testGetLatestVersion(self):
    """Tests the GetLatestVersion functions."""
    download_helper_object = download_helper.GitHubReleasesDownloadHelper(
        self._DOWNLOAD_URL)

    latest_version = download_helper_object.GetLatestVersion(
        self._PROJECT_NAME, None)

    self.assertEqual(latest_version, self._PROJECT_VERSION)

  def testGetDownloadURL(self):
    """Tests the GetDownloadURL functions."""
    download_helper_object = download_helper.GitHubReleasesDownloadHelper(
        self._DOWNLOAD_URL)

    download_url = download_helper_object.GetDownloadURL(
        self._PROJECT_NAME, self._PROJECT_VERSION)

    expected_download_url = (
        'https://github.com/{0:s}/{1:s}/releases/download/{2:s}/'
        '{1:s}-{2:s}.tar.gz').format(
            self._PROJECT_ORGANIZATION, self._PROJECT_NAME,
            self._PROJECT_VERSION)

    self.assertEqual(download_url, expected_download_url)

  def testGetProjectIdentifier(self):
    """Tests the GetProjectIdentifier functions."""
    download_helper_object = download_helper.GitHubReleasesDownloadHelper(
        self._DOWNLOAD_URL)

    project_identifier = download_helper_object.GetProjectIdentifier()

    expected_project_identifier = 'com.github.{0:s}.{1:s}'.format(
        self._PROJECT_ORGANIZATION, self._PROJECT_NAME)

    self.assertEqual(project_identifier, expected_project_identifier)


class PyPIDownloadHelperTest(unittest.TestCase):
  """Tests for the PyPi download helper."""

  _DOWNLOAD_URL = 'https://pypi.python.org/pypi/construct'

  _PROJECT_NAME = 'construct'
  _PROJECT_VERSION = '2.8.16'

  def testGetLatestVersion(self):
    """Tests the GetLatestVersion functions."""
    download_helper_object = download_helper.PyPIDownloadHelper(
        self._DOWNLOAD_URL)

    latest_version = download_helper_object.GetLatestVersion(
        self._PROJECT_NAME, None)

    self.assertEqual(latest_version, self._PROJECT_VERSION)

  def testGetDownloadURL(self):
    """Tests the GetDownloadURL functions."""
    download_helper_object = download_helper.PyPIDownloadHelper(
        self._DOWNLOAD_URL)

    download_url = download_helper_object.GetDownloadURL(
        self._PROJECT_NAME, self._PROJECT_VERSION)

    test_regexp = (
        r'/packages\/\w{{2}}\/\w{{2}}\/\w+\/{0:s}-{1:s}\.tar\.gz').format(
            self._PROJECT_NAME, self._PROJECT_VERSION)

    # pylint: disable=deprecated-method
    # TODO: replace assertRegexpMatches by assertRegexp, check if compatible
    # with Python 2 first.
    self.assertRegexpMatches(download_url, test_regexp)

  def testGetProjectIdentifier(self):
    """Tests the GetProjectIdentifier functions."""
    download_helper_object = download_helper.PyPIDownloadHelper(
        self._DOWNLOAD_URL)

    project_identifier = download_helper_object.GetProjectIdentifier()

    expected_project_identifier = 'org.python.pypi.{0:s}'.format(
        self._PROJECT_NAME)

    self.assertEqual(project_identifier, expected_project_identifier)


class SourceForgeDownloadHelperTest(unittest.TestCase):
  """Tests for the Source Forge download helper."""

  _DOWNLOAD_URL = 'https://sourceforge.net/projects/pyparsing/files'

  _PROJECT_NAME = 'pyparsing'
  # Hard-coded version to check parsing of SourceForge page.
  _PROJECT_VERSION = '2.2.0'

  def testGetLatestVersion(self):
    """Tests the GetLatestVersion functions."""
    download_helper_object = download_helper.SourceForgeDownloadHelper(
        self._DOWNLOAD_URL)

    latest_version = download_helper_object.GetLatestVersion(
        self._PROJECT_NAME, None)

    self.assertEqual(latest_version, self._PROJECT_VERSION)

  def testGetDownloadURL(self):
    """Tests the GetDownloadURL functions."""
    download_helper_object = download_helper.SourceForgeDownloadHelper(
        self._DOWNLOAD_URL)

    download_url = download_helper_object.GetDownloadURL(
        self._PROJECT_NAME, self._PROJECT_VERSION)

    expected_download_url = (
        'https://downloads.sourceforge.net/project/{0:s}/{0:s}/{0:s}-{1:s}'
        '/{0:s}-{1:s}.tar.gz').format(
            self._PROJECT_NAME, self._PROJECT_VERSION)

    self.assertEqual(download_url, expected_download_url)

  def testGetProjectIdentifier(self):
    """Tests the GetProjectIdentifier functions."""
    download_helper_object = download_helper.SourceForgeDownloadHelper(
        self._DOWNLOAD_URL)

    project_identifier = download_helper_object.GetProjectIdentifier()

    expected_project_identifier = 'net.sourceforge.projects.{0:s}'.format(
        self._PROJECT_NAME)

    self.assertEqual(project_identifier, expected_project_identifier)


if __name__ == '__main__':
  unittest.main()
