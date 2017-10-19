#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tests for the upload helper."""

from __future__ import unicode_literals

import unittest

import l2tdevtools.helpers.upload as upload_helper


class UploadHelperTest(unittest.TestCase):
  """Tests the upload helper"""

  def testInitialize(self):
    """Tests that the helper can be initialized."""
    helper = upload_helper.UploadHelper(email_address='onager@deerpie.com')
    self.assertIsNotNone(helper)


if __name__ == '__main__':
  unittest.main()
