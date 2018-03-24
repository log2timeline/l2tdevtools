#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tests for the helper for building projects from source."""

from __future__ import unicode_literals

import unittest

from l2tdevtools.build_helpers import interface
from l2tdevtools import projects


class BuildHelperTest(unittest.TestCase):
  """Tests for the helper to build projects from source."""

  def testCheckBuildDependencies(self):
    """Tests the CheckBuildDependencies function."""
    project_definition = projects.ProjectDefinition('test')
    build_helper = interface.BuildHelper(project_definition, '')

    build_dependencies = build_helper.CheckBuildDependencies()
    self.assertEqual(build_dependencies, [])

  def testCheckBuildRequired(self):
    """Tests the CheckBuildRequired function."""
    project_definition = projects.ProjectDefinition('test')
    build_helper = interface.BuildHelper(project_definition, '')

    result = build_helper.CheckBuildRequired(None)
    self.assertTrue(result)


if __name__ == '__main__':
  unittest.main()
