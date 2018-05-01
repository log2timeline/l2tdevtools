#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tests for the project preset definitions."""

from __future__ import unicode_literals

import unittest

from l2tdevtools import presets

from tests import test_lib


class PresetDefinitionTest(test_lib.BaseTestCase):
  """Tests for the preset definition."""

  def testInitialize(self):
    """Tests the __init__ function."""
    preset_definition = presets.PresetDefinition('test')
    self.assertIsNotNone(preset_definition)


# TODO: add tests.


if __name__ == '__main__':
  unittest.main()
