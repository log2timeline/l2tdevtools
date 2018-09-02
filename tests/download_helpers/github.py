#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tests for the download helper object implementations."""

from __future__ import unicode_literals

import os
import unittest

from l2tdevtools.download_helpers import github

from tests import test_lib


@unittest.skipIf(
    os.environ.get('TRAVIS_OS_NAME') == 'osx',
    'TLS 1.2 not supported by macOS on Travis')
class DocoptGitHubReleasesDownloadHelperTest(test_lib.BaseTestCase):
  """Tests for the docopt GitHub releases download helper."""

  _DOWNLOAD_URL = 'https://github.com/docopt/docopt/releases'

  _PROJECT_ORGANIZATION = 'docopt'
  _PROJECT_NAME = 'docopt'
  _PROJECT_VERSION = '0.6.2'

  def testGetLatestVersion(self):
    """Tests the GetLatestVersion functions."""
    download_helper = github.GitHubReleasesDownloadHelper(self._DOWNLOAD_URL)

    latest_version = download_helper.GetLatestVersion(self._PROJECT_NAME, None)

    self.assertEqual(latest_version, self._PROJECT_VERSION)

  def testGetDownloadURL(self):
    """Tests the GetDownloadURL functions."""
    download_helper = github.GitHubReleasesDownloadHelper(self._DOWNLOAD_URL)

    download_url = download_helper.GetDownloadURL(
        self._PROJECT_NAME, self._PROJECT_VERSION)

    expected_download_url = (
        'https://github.com/{0:s}/{1:s}/archive/{2:s}.tar.gz').format(
            self._PROJECT_ORGANIZATION, self._PROJECT_NAME,
            self._PROJECT_VERSION)

    self.assertEqual(download_url, expected_download_url)

  def testGetProjectIdentifier(self):
    """Tests the GetProjectIdentifier functions."""
    download_helper = github.GitHubReleasesDownloadHelper(self._DOWNLOAD_URL)

    project_identifier = download_helper.GetProjectIdentifier()

    expected_project_identifier = 'com.github.{0:s}.{1:s}'.format(
        self._PROJECT_ORGANIZATION, self._PROJECT_NAME)

    self.assertEqual(project_identifier, expected_project_identifier)


@unittest.skipIf(
    os.environ.get('TRAVIS_OS_NAME') == 'osx',
    'TLS 1.2 not supported by macOS on Travis')
class LibyalGitHubReleasesDownloadHelperTest(test_lib.BaseTestCase):
  """Tests for the libyal GitHub releases download helper."""

  _DOWNLOAD_URL = 'https://github.com/libyal/libevt/releases'

  _PROJECT_ORGANIZATION = 'libyal'
  _PROJECT_NAME = 'libevt'
  _PROJECT_STATUS = 'alpha'
  _PROJECT_VERSION = '20180317'

  def testGetLatestVersion(self):
    """Tests the GetLatestVersion functions."""
    download_helper = github.GitHubReleasesDownloadHelper(self._DOWNLOAD_URL)

    latest_version = download_helper.GetLatestVersion(self._PROJECT_NAME, None)

    self.assertEqual(latest_version, self._PROJECT_VERSION)

  def testGetDownloadURL(self):
    """Tests the GetDownloadURL functions."""
    download_helper = github.GitHubReleasesDownloadHelper(self._DOWNLOAD_URL)

    download_url = download_helper.GetDownloadURL(
        self._PROJECT_NAME, self._PROJECT_VERSION)

    expected_download_url = (
        'https://github.com/{0:s}/{1:s}/releases/download/{3:s}/'
        '{1:s}-{2:s}-{3:s}.tar.gz').format(
            self._PROJECT_ORGANIZATION, self._PROJECT_NAME,
            self._PROJECT_STATUS, self._PROJECT_VERSION)

    self.assertEqual(download_url, expected_download_url)

  def testGetProjectIdentifier(self):
    """Tests the GetProjectIdentifier functions."""
    download_helper = github.GitHubReleasesDownloadHelper(self._DOWNLOAD_URL)

    project_identifier = download_helper.GetProjectIdentifier()

    expected_project_identifier = 'com.github.{0:s}.{1:s}'.format(
        self._PROJECT_ORGANIZATION, self._PROJECT_NAME)

    self.assertEqual(project_identifier, expected_project_identifier)


@unittest.skipIf(
    os.environ.get('TRAVIS_OS_NAME') == 'osx',
    'TLS 1.2 not supported by macOS on Travis')
class Log2TimelineGitHubReleasesDownloadHelperTest(test_lib.BaseTestCase):
  """Tests for the log2timeline GitHub releases download helper."""

  _DOWNLOAD_URL = 'https://github.com/log2timeline/dfvfs/releases'

  _PROJECT_ORGANIZATION = 'log2timeline'
  _PROJECT_NAME = 'dfvfs'
  # Hard-coded version to check parsing of GitHub page.
  _PROJECT_VERSION = '20180831'

  def testGetLatestVersion(self):
    """Tests the GetLatestVersion functions."""
    download_helper = github.GitHubReleasesDownloadHelper(self._DOWNLOAD_URL)

    latest_version = download_helper.GetLatestVersion(self._PROJECT_NAME, None)

    self.assertEqual(latest_version, self._PROJECT_VERSION)

  def testGetDownloadURL(self):
    """Tests the GetDownloadURL functions."""
    download_helper = github.GitHubReleasesDownloadHelper(self._DOWNLOAD_URL)

    download_url = download_helper.GetDownloadURL(
        self._PROJECT_NAME, self._PROJECT_VERSION)

    expected_download_url = (
        'https://github.com/{0:s}/{1:s}/releases/download/{2:s}/'
        '{1:s}-{2:s}.tar.gz').format(
            self._PROJECT_ORGANIZATION, self._PROJECT_NAME,
            self._PROJECT_VERSION)

    self.assertEqual(download_url, expected_download_url)

  def testGetProjectIdentifier(self):
    """Tests the GetProjectIdentifier functions."""
    download_helper = github.GitHubReleasesDownloadHelper(self._DOWNLOAD_URL)

    project_identifier = download_helper.GetProjectIdentifier()

    expected_project_identifier = 'com.github.{0:s}.{1:s}'.format(
        self._PROJECT_ORGANIZATION, self._PROJECT_NAME)

    self.assertEqual(project_identifier, expected_project_identifier)


if __name__ == '__main__':
  unittest.main()
