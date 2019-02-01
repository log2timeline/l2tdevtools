#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tests for the update tool."""

from __future__ import unicode_literals

import os
import sys
import unittest

from tools import update

from tests import test_lib


@unittest.skipIf(
    os.environ.get('TRAVIS_OS_NAME') == 'osx',
    'TLS 1.2 not supported by macOS on Travis')
class GithubRepoDownloadHelperTest(test_lib.BaseTestCase):
  """Tests for the GitHub repo download helper class."""

  _DOWNLOAD_URL = 'https://github.com/ForensicArtifacts/artifacts/releases'

  _PROJECT_NAME = 'artifacts'
  _PROJECT_VERSION = '20190113'

  def testGetPackageDownloadURLs(self):
    """Tests the GetPackageDownloadURLs function."""
    download_helper = update.GithubRepoDownloadHelper(self._DOWNLOAD_URL)

    package_download_urls = download_helper.GetPackageDownloadURLs(
        preferred_machine_type='x86', preferred_operating_system='Windows')

    if (sys.version_info[0] not in (2, 3) or
        (sys.version_info[0] == 2 and sys.version_info[1] != 7) or
        (sys.version_info[0] == 3 and sys.version_info[1] != 6)):

      # Python versions other than 2.7 and 3.6 are not supported.
      self.assertIsNone(package_download_urls)

    else:
      self.assertIsNotNone(package_download_urls)

      expected_url = (
          'https://github.com/log2timeline/l2tbinaries/raw/master/win32/'
          '{0:s}-{1:s}.1.win32.msi').format(
              self._PROJECT_NAME, self._PROJECT_VERSION)
      self.assertIn(expected_url, package_download_urls)


@unittest.skipIf(
    os.environ.get('TRAVIS_OS_NAME') == 'osx',
    'TLS 1.2 not supported by macOS on Travis')
class DependencyUpdaterTest(test_lib.BaseTestCase):
  """Tests for the dependency updater class."""

  # pylint: disable=protected-access

  _PROJECT_NAME = 'dfvfs'
  _PROJECT_VERSION = '20190128'

  def testGetAvailablePackages(self):
    """Tests the _GetAvailablePackages function."""
    dependency_updater = update.DependencyUpdater(
        preferred_machine_type='x86', preferred_operating_system='Windows')

    available_packages = dependency_updater._GetAvailablePackages()

    if (sys.version_info[0] not in (2, 3) or
        (sys.version_info[0] == 2 and sys.version_info[1] != 7) or
        (sys.version_info[0] == 3 and sys.version_info[1] != 6)):

      # Python versions other than 2.7 and 3.6 are not supported.
      self.assertEqual(available_packages, [])

    else:
      self.assertNotEqual(available_packages, [])

      for package_download in available_packages:
        if package_download.name == self._PROJECT_NAME:
          expected_package_filename = '{0:s}-{1:s}.1.win32.msi'.format(
              self._PROJECT_NAME, self._PROJECT_VERSION)
          self.assertEqual(package_download.filename, expected_package_filename)

          expected_package_version = [self._PROJECT_VERSION, '1']
          self.assertEqual(package_download.version, expected_package_version)


if __name__ == '__main__':
  unittest.main()
