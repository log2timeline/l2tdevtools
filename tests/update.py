#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the update tool."""

import unittest

from tools import update


class GithubRepoDownloadHelperTest(unittest.TestCase):
  """Tests for the github repo download helper class."""

  _DOWNLOAD_URL = u'https://github.com/ForensicArtifacts/artifacts/releases'

  _PROJECT_NAME = u'artifacts'
  _PROJECT_VERSION = u'20161022'

  def testGetPackageDownloadURLs(self):
    """Tests the GetPackageDownloadURLs function."""
    download_helper = update.GithubRepoDownloadHelper(self._DOWNLOAD_URL)

    package_download_urls = download_helper.GetPackageDownloadURLs(
        preferred_machine_type=u'x86', preferred_operating_system=u'Windows')

    expected_url = (
        u'https://github.com/log2timeline/l2tbinaries/raw/master/win32/'
        u'{0:s}-{1:s}.1.win32.msi').format(
            self._PROJECT_NAME, self._PROJECT_VERSION)
    self.assertIn(expected_url, package_download_urls)


class DependencyUpdaterTest(unittest.TestCase):
  """Tests for the dependency updater class."""

  _PROJECT_NAME = u'dfvfs'
  _PROJECT_VERSION = u'20170116'

  def testGetPackageFilenamesAndVersions(self):
    """Tests the GetPackageFilenamesAndVersions function."""
    dependency_updater = update.DependencyUpdater(
        preferred_machine_type=u'x86', preferred_operating_system=u'Windows')

    # pylint: disable=protected-access
    package_filenames, package_versions = (
        dependency_updater._GetPackageFilenamesAndVersions([]))

    self.assertEqual(
        package_filenames.get(self._PROJECT_NAME, None),
        u'{0:s}-{1:s}.1.win32.msi'.format(
            self._PROJECT_NAME, self._PROJECT_VERSION))

    self.assertEqual(
        package_versions.get(self._PROJECT_NAME, None),
        [self._PROJECT_VERSION, u'1'])


if __name__ == '__main__':
  unittest.main()
