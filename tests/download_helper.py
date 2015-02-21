#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the download helper object implementations."""

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
    self.name = u''

  def __enter__(self):
    """Make this work with the 'with' statement."""
    self.name = tempfile.mkdtemp()
    return self.name

  def __exit__(self, unused_type, unused_value, unused_traceback):
    """Make this work with the 'with' statement."""
    shutil.rmtree(self.name, True)


class DownloadHelperTest(unittest.TestCase):
  """Tests for the download helper."""

  _FILENAME = u'LICENSE'

  def setUp(self):
    """Sets up a test case."""
    self._download_url = (
        u'https://raw.githubusercontent.com/log2timeline/devtools/master/'
        u'{0:s}').format(self._FILENAME)

  def testDownloadPageContent(self):
    """Tests the DownloadPageContent functions."""
    download_helper_object = download_helper.DownloadHelper()

    page_content = download_helper_object.DownloadPageContent(
        self._download_url)

    expected_page_content = b''
    with open(self._FILENAME, 'rb') as file_object:
      expected_page_content = file_object.read()

    self.assertEquals(page_content, expected_page_content)

  def testDownloadFile(self):
    """Tests the DownloadFile functions."""
    download_helper_object = download_helper.DownloadHelper()

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

    self.assertEquals(page_content, expected_page_content)


class GoogleCodeWikiDownloadHelperTest(unittest.TestCase):
  """Tests for the Google code wiki download helper."""

  _PROJECT_NAME = u'binplist'
  _PROJECT_VERSION = u'0.1.4'

  def testGetLatestVersion(self):
    """Tests the GetLatestVersion functions."""
    download_helper_object = download_helper.GoogleCodeWikiDownloadHelper()

    latest_version = download_helper_object.GetLatestVersion(self._PROJECT_NAME)

    self.assertEquals(latest_version, self._PROJECT_VERSION)

  def testGetDownloadUrl(self):
    """Tests the GetDownloadUrl functions."""
    download_helper_object = download_helper.GoogleCodeWikiDownloadHelper()

    download_url = download_helper_object.GetDownloadUrl(
        self._PROJECT_NAME, self._PROJECT_VERSION)

    expected_download_url = (
        u'https://{0:s}.googlecode.com/files/{0:s}-{1:s}.tar.gz').format(
            self._PROJECT_NAME, self._PROJECT_VERSION)

    self.assertEquals(download_url, expected_download_url)

  def testGetProjectIdentifier(self):
    """Tests the GetProjectIdentifier functions."""
    download_helper_object = download_helper.GoogleCodeWikiDownloadHelper()

    project_identifier = download_helper_object.GetProjectIdentifier(
        self._PROJECT_NAME)

    expected_project_identifier = u'com.google.code.p.{0:s}'.format(
        self._PROJECT_NAME)

    self.assertEquals(project_identifier, expected_project_identifier)


class LibyalGoogleDriveDownloadHelperTest(unittest.TestCase):
  """Tests for the libyal Google drive download helper."""


class LibyalGithubReleasesDownloadHelperTest(unittest.TestCase):
  """Tests for the libyal github releases download helper."""


class Log2TimelineGitHubDownloadHelperTest(unittest.TestCase):
  """Tests for the log2timeline github download helper."""


class PyPiDownloadHelperTest(unittest.TestCase):
  """Tests for the PyPi download helper."""


class SourceForgeDownloadHelperTest(unittest.TestCase):
  """Tests for the Source Forge download helper."""
