#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tests for the elper for managing project source code."""

from __future__ import unicode_literals

import unittest

from l2tdevtools import source_helper

from tests import test_lib


class SourceHelperTest(test_lib.BaseTestCase):
  """Tests for the helper to manager project source code."""

  def testInitialize(self):
    """Tests the __init__ function."""
    source_helper_object = source_helper.SourceHelper('test', None)
    self.assertIsNotNone(source_helper_object)


# TODO: add tests.


if __name__ == '__main__':
  unittest.main()
