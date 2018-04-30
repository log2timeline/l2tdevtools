#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tests for the download helper object implementations."""

from __future__ import unicode_literals

import os
import unittest

from l2tdevtools.download_helpers import interface

from tests import test_lib


class DownloadHelperTest(test_lib.BaseTestCase):
  """Tests for the download helper."""

  _FILENAME = 'LICENSE'

  def setUp(self):
    """Sets up a test case."""
    self._download_url = (
        'https://raw.githubusercontent.com/log2timeline/l2tdevtools/master/'
        '{0:s}').format(self._FILENAME)

  def testDownloadPageContent(self):
    """Tests the DownloadPageContent functions."""
    download_helper = interface.DownloadHelper('')

    page_content = download_helper.DownloadPageContent(self._download_url)

    expected_page_content = b''
    with open(self._FILENAME, 'rb') as file_object:
      expected_page_content = file_object.read()
      expected_page_content = expected_page_content.decode('utf-8')

    self.assertEqual(page_content, expected_page_content)

  def testDownloadFile(self):
    """Tests the DownloadFile functions."""
    download_helper = interface.DownloadHelper(self._download_url)

    current_working_directory = os.getcwd()

    page_content = b''
    with test_lib.TempDirectory() as temporary_directory:
      os.chdir(temporary_directory)
      filename = download_helper.DownloadFile(self._download_url)

      with open(filename, 'rb') as file_object:
        page_content = file_object.read()

    os.chdir(current_working_directory)

    expected_page_content = b''
    with open(self._FILENAME, 'rb') as file_object:
      expected_page_content = file_object.read()

    self.assertEqual(page_content, expected_page_content)


if __name__ == '__main__':
  unittest.main()
