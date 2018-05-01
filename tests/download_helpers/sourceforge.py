#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tests for the download helper object implementations."""

from __future__ import unicode_literals

import os
import unittest

from l2tdevtools.download_helpers import sourceforge

from tests import test_lib


@unittest.skipIf(
    os.environ.get('APPVEYOR', ''), 'Test is flaky for Windows on AppVeyor')
@unittest.skipIf(
    os.environ.get('TRAVIS_OS_NAME') == 'osx',
    'TLS 1.2 not supported by macOS on Travis')
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

    expected_download_url = (
        'https://downloads.sourceforge.net/project/{0:s}/{0:s}/{0:s}-{1:s}'
        '/{0:s}-{1:s}.tar.gz').format(
            self._PROJECT_NAME, self._PROJECT_VERSION)

    self.assertEqual(download_url, expected_download_url)

  def testGetProjectIdentifier(self):
    """Tests the GetProjectIdentifier functions."""
    download_helper = sourceforge.SourceForgeDownloadHelper(self._DOWNLOAD_URL)

    project_identifier = download_helper.GetProjectIdentifier()

    expected_project_identifier = 'net.sourceforge.projects.{0:s}'.format(
        self._PROJECT_NAME)

    self.assertEqual(project_identifier, expected_project_identifier)


if __name__ == '__main__':
  unittest.main()
