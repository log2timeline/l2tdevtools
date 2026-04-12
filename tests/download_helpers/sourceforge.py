#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the download helper object implementations."""

import os
import unittest

from l2tdevtools.download_helpers import sourceforge

from tests import test_lib


@unittest.skipIf(
    os.environ.get('APPVEYOR', ''), 'Test is flaky for Windows on AppVeyor')
class SourceForgeDownloadHelperTest(test_lib.BaseTestCase):
  """Tests for the Source Forge download helper."""

  _DOWNLOAD_URL = 'https://sourceforge.net/projects/pyparsing/files'

  _PROJECT_NAME = 'pyparsing'
  # Hard-coded version to check parsing of SourceForge page.
  _PROJECT_VERSION = '2.2.0'

  def testGetLatestVersion(self):
    """Tests the GetLatestVersion functions."""
    download_helper = sourceforge.SourceForgeDownloadHelper(self._DOWNLOAD_URL)

    latest_version = download_helper.GetLatestVersion(self._PROJECT_NAME, None)

    self.assertEqual(latest_version, self._PROJECT_VERSION)

  def testGetDownloadURL(self):
    """Tests the GetDownloadURL functions."""
    download_helper = sourceforge.SourceForgeDownloadHelper(self._DOWNLOAD_URL)

    download_url = download_helper.GetDownloadURL(
        self._PROJECT_NAME, self._PROJECT_VERSION)

    project_name = self._PROJECT_NAME
    project_version = self._PROJECT_VERSION
    expected_download_url = (
        f'https://downloads.sourceforge.net/project/{project_name:s}/'
        f'{project_name:s}/{project_name:s}-{project_version:s}/'
        f'{project_name:s}-{project_version:s}.tar.gz')

    self.assertEqual(download_url, expected_download_url)

  def testGetProjectIdentifier(self):
    """Tests the GetProjectIdentifier functions."""
    download_helper = sourceforge.SourceForgeDownloadHelper(self._DOWNLOAD_URL)

    project_identifier = download_helper.GetProjectIdentifier()

    expected_project_identifier = (
        f'net.sourceforge.projects.{self._PROJECT_NAME:s}')

    self.assertEqual(project_identifier, expected_project_identifier)


if __name__ == '__main__':
  unittest.main()
