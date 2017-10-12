# -*- coding: utf-8 -*-
"""Tests for the upload helper."""
import unittest

import l2tdevtools.helpers.upload as upload_helper


class UploadHelperTest(unittest.TestCase):
  """Tests the upload helper"""

  def testInitialize(self):
    """Tests that the helper can be initialized."""
    helper = upload_helper.UploadHelper(email_address=u'onager@deerpie.com')
    self.assertIsNotNone(helper)
