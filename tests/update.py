#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the update tool."""

import unittest

from tools import update


class GithubRepoDownloadHelperTest(unittest.TestCase):
  """Tests for the github repo download helper class."""

  def testGetPackageDownloadURLs(self):
    """Tests the GetPackageDownloadURLs functions."""
    download_helper = update.GithubRepoDownloadHelper()

    package_download_urls = download_helper.GetPackageDownloadURLs(
        preferred_machine_type=u'x86', preferred_operating_system=u'Windows')

    expected_url = (
        u'https://github.com/log2timeline/l2tbinaries/raw/master/win32/'
        u'artifacts-20150409.1.win32.msi')
    self.assertIn(expected_url, package_download_urls)


class DependencyUpdaterTest(unittest.TestCase):
  """Tests for the dependency updater class."""

  def testGetPackageFilenamesAndVersions(self):
    """Tests the GetPackageFilenamesAndVersions functions."""
    dependency_updater = update.DependencyUpdater(
        preferred_machine_type=u'x86', preferred_operating_system=u'Windows')

    package_filenames, package_versions = (
        dependency_updater._GetPackageFilenamesAndVersions())

    self.assertEqual(
        package_filenames.get(u'dfvfs', None), u'dfvfs-20150915.1.win32.msi')

    self.assertEqual(package_versions.get(u'dfvfs', None), [u'20150915', u'1'])


if __name__ == '__main__':
  unittest.main()
