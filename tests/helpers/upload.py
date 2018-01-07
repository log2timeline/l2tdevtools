#!/usr/bin/env python
# *- coding: utf-8 *-
"""Tests for the upload helper."""

from __future__ import unicode_literals

import os
import unittest

import l2tdevtools.helpers.upload as upload_helper


class UploadHelperTest(unittest.TestCase):
  """Tests the upload helper"""

  def testInitialize(self):
    """Tests that the helper can be initialized."""
    helper = upload_helper.UploadHelper(email_address='onager@deerpie.com')
    self.assertIsNotNone(helper)

  # TODO: add test for AddMergeMessage
  # TODO: add test for CloseIssue
  # TODO: add test for CreateIssue
  # TODO: add test for GetAccessToken

  @unittest.skipIf(
      os.environ.get('TRAVIS_OS_NAME', ''), 'Travis-CI not supported')
  def testGetXSRFToken(self):
    """Tests the GetXSRFToken function."""
    helper = upload_helper.UploadHelper(
        email_address='test@example.com', no_browser=True)

    # Only test if the method completes without errors.
    helper.GetXSRFToken()

  def testQueryIssue(self):
    """Tests the QueryIssue function."""
    helper = upload_helper.UploadHelper(
        email_address='test@example.com', no_browser=True)

    codereview_information = helper.QueryIssue(269830043)
    self.assertIsNotNone(codereview_information)

    expected_description = (
        'Updated review scripts and added Python variant #40')
    description = codereview_information.get('subject')
    self.assertEqual(description, expected_description)

    codereview_information = helper.QueryIssue(0)
    self.assertIsNone(codereview_information)

    codereview_information = helper.QueryIssue(1)
    self.assertIsNone(codereview_information)

  # TODO: add test for UpdateIssue


if __name__ == '__main__':
  unittest.main()
