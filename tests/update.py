#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tests for the update tool."""

import glob
import os
import sys
import unittest

from tools import update

from tests import test_lib


class GithubRepoDownloadHelperTest(test_lib.BaseTestCase):
  """Tests for the GitHub repo download helper class."""

  # pylint: disable=protected-access

  _DOWNLOAD_URL = 'https://github.com/ForensicArtifacts/artifacts/releases'

  _PROJECT_NAME = 'artifacts'
  _PROJECT_VERSION = '20240303'

  def testGetPackageDownloadURLs(self):
    """Tests the GetPackageDownloadURLs function."""
    download_helper = update.GithubRepoDownloadHelper(
        self._DOWNLOAD_URL, branch='dev')

    package_download_urls = download_helper.GetPackageDownloadURLs(
        preferred_machine_type='x86', preferred_operating_system='Windows')

    if (sys.version_info[0], sys.version_info[1]) not in (
        download_helper._SUPPORTED_PYTHON_VERSIONS):
      self.assertIsNone(package_download_urls)

    else:
      self.assertIsNotNone(package_download_urls)

      expected_url = (
          'https://github.com/log2timeline/l2tbinaries/raw/dev/win32/'
          '{0:s}-{1:s}-py2.py3-none-any.whl').format(
              self._PROJECT_NAME, self._PROJECT_VERSION)
      self.assertIn(expected_url, package_download_urls)


class DependencyUpdaterTest(test_lib.BaseTestCase):
  """Tests for the dependency updater class."""

  # pylint: disable=protected-access

  _PROJECT_NAME = 'dfvfs'
  _PROJECT_VERSION = '20240115'

  def testGetAvailableWheelPackages(self):
    """Tests the _GetAvailableWheelPackages function."""
    dependency_updater = update.DependencyUpdater(
        download_track='dev', preferred_machine_type='x86',
        preferred_operating_system='Windows')

    available_packages = dependency_updater._GetAvailableWheelPackages()

    if (sys.version_info[0], sys.version_info[1]) not in (
        update.GithubRepoDownloadHelper._SUPPORTED_PYTHON_VERSIONS):
      self.assertEqual(available_packages, [])

    else:
      self.assertNotEqual(available_packages, [])

      for package_download in available_packages:
        if package_download.name == self._PROJECT_NAME:
          expected_package_filename = '{0:s}-{1:s}-py2.py3-none-any.whl'.format(
              self._PROJECT_NAME, self._PROJECT_VERSION)
          self.assertEqual(package_download.filename, expected_package_filename)

          expected_package_version = [self._PROJECT_VERSION]
          self.assertEqual(package_download.version, expected_package_version)

  def testUpdatePackages(self):
    """Tests the UpdatePackages function."""
    projects_file = os.path.join('data', 'projects.ini')

    if (sys.version_info[0], sys.version_info[1]) in (
        update.GithubRepoDownloadHelper._SUPPORTED_PYTHON_VERSIONS):
      with test_lib.TempDirectory() as temp_directory:
        dependency_updater = update.DependencyUpdater(
            download_directory=temp_directory, download_only=True,
            download_track='dev', preferred_machine_type='x86',
            preferred_operating_system='Windows')

        dependency_updater.UpdatePackages(projects_file, [self._PROJECT_NAME])

        glob_results = sorted(glob.glob(os.path.join(temp_directory, '*.whl')))

        self.assertEqual(len(glob_results), 1)

        expected_path = os.path.join(
            temp_directory, '{0:s}-{1:s}-py2.py3-none-any.whl'.format(
                self._PROJECT_NAME, self._PROJECT_VERSION))
        self.assertEqual(glob_results[0], expected_path)


if __name__ == '__main__':
  unittest.main()
