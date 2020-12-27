#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tests for the helper for building projects from source."""

from __future__ import unicode_literals

import os
import unittest

from l2tdevtools import build_helper
from l2tdevtools import projects

from tests import test_lib


class BuildHelperFactoryTest(test_lib.BaseTestCase):
  """Tests the factory class for build helpers."""

  def testNewBuildHelper(self):
    """Tests the NewBuildHelper function."""
    project_definition = projects.ProjectDefinition('test')

    l2tdevtools_path = os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))))

    build_helper_object = build_helper.BuildHelperFactory.NewBuildHelper(
        project_definition, 'source', l2tdevtools_path, {})
    self.assertIsNone(build_helper_object)

    project_definition.build_system = 'setup_py'
    build_helper_object = build_helper.BuildHelperFactory.NewBuildHelper(
        project_definition, 'source', l2tdevtools_path, {})
    self.assertIsNotNone(build_helper_object)

    build_helper_object = build_helper.BuildHelperFactory.NewBuildHelper(
        project_definition, 'bogus', l2tdevtools_path, {})
    self.assertIsNone(build_helper_object)


if __name__ == '__main__':
  unittest.main()
