#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the elper for managing project source code."""

import unittest

from l2tdevtools import source_helper


class SourceHelperTest(unittest.TestCase):
  """Tests for the helper to manager project source code."""

  def testInitialize(self):
    """Tests the __init__ function."""
    source_helper_object = source_helper.SourceHelper(u'test', None)
    self.assertIsNotNone(source_helper_object)


# TODO: add tests.


if __name__ == '__main__':
  unittest.main()
