#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tests for the sphinxapi helper."""

from __future__ import unicode_literals

import unittest

import l2tdevtools.helpers.sphinxapi as sphinxapi_helper


class SphinxapiHelperTest(unittest.TestCase):
  """Tests the sphinxapi helper"""

  def testInitialize(self):
    """Tests that the helper can be initialized."""
    helper = sphinxapi_helper.SphinxAPIDocHelper(project='test')
    self.assertIsNotNone(helper)


if __name__ == '__main__':
  unittest.main()
