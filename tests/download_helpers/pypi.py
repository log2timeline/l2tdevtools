#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tests for the download helper object implementations."""

import re
import shlex
import subprocess
import unittest

from l2tdevtools.download_helpers import pypi

from tests import test_lib


class PyPIDownloadHelperTest(test_lib.BaseTestCase):
  """Tests for the PyPi download helper."""

  _DOWNLOAD_URL = 'https://pypi.org/project/dfvfs'
  _GIT_URL = 'https://github.com/log2timeline/dfvfs.git'

  _PROJECT_NAME = 'dfvfs'
  _PROJECT_VERSION = '20230407'
  _PYPI_VERSION = '20230407'

  @classmethod
  def setUpClass(cls):
    """Determines the project version from the latest git tag."""
    command = 'git ls-remote --tags {0:s}'.format(cls._GIT_URL)
    arguments = shlex.split(command)

    try:
      with subprocess.Popen(
          arguments, stderr=subprocess.PIPE, stdout=subprocess.PIPE) as process:
        output, _ = process.communicate()
        if process.returncode != 0:
          return

    except OSError:
      return

    output = output.decode('ascii')

    latest_version = '0'
    for line in output.split('\n'):
      line = line.strip()
      if 'refs/tags/' in line and not line.endswith('^{}'):
        _, _, version = line.rpartition('refs/tags/')
        latest_version = max(latest_version, version)

    cls._PROJECT_VERSION = latest_version

  def testGetLatestVersion(self):
    """Tests the GetLatestVersion functions."""
    download_helper = pypi.PyPIDownloadHelper(self._DOWNLOAD_URL)

    latest_version = download_helper.GetLatestVersion(self._PROJECT_NAME, None)

    self.assertEqual(latest_version, self._PYPI_VERSION)

  def testGetDownloadURL(self):
    """Tests the GetDownloadURL functions."""
    download_helper = pypi.PyPIDownloadHelper(self._DOWNLOAD_URL)

    expected_download_url_regexp = re.compile(
        r'https://files.pythonhosted.org/packages/'
        r'[\da-f/]+{0:s}-\d{{8}}.tar.gz'.format(self._PROJECT_NAME))

    download_url = download_helper.GetDownloadURL(
        self._PROJECT_NAME, self._PYPI_VERSION)

    self.assertRegex(download_url, expected_download_url_regexp)

  def testGetProjectIdentifier(self):
    """Tests the GetProjectIdentifier functions."""
    download_helper = pypi.PyPIDownloadHelper(self._DOWNLOAD_URL)

    project_identifier = download_helper.GetProjectIdentifier()

    expected_project_identifier = 'org.pypi.{0:s}'.format(
        self._PROJECT_NAME)

    self.assertEqual(project_identifier, expected_project_identifier)


if __name__ == '__main__':
  unittest.main()
