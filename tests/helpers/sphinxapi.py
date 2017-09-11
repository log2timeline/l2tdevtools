# -*- coding: utf-8 -*-
"""Tests for the sphinxapi helper."""
import unittest

import l2tdevtools.helpers.sphinxapi as sphinxapi_helper


class SphinxapiHelperTest(unittest.TestCase):
  """Tests the sphinxapi helper"""

  def testInitialize(self):
    """Tests that the helper can be initialized."""
    helper = sphinxapi_helper.SphinxAPIDocHelper(project=u'test')
    self.assertIsNotNone(helper)
