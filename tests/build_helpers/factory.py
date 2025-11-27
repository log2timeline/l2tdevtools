#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the helper for building projects from source."""

import os
import unittest

from l2tdevtools import projects
from l2tdevtools.build_helpers import factory

from tests import test_lib


class BuildHelperFactoryTest(test_lib.BaseTestCase):
  """Tests the factory class for build helpers."""

  def testNewBuildHelper(self):
    """Tests the NewBuildHelper function."""
    project_definition = projects.ProjectDefinition('test')

    l2tdevtools_path = os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))))

    build_helper = factory.BuildHelperFactory.NewBuildHelper(
        project_definition, 'source', l2tdevtools_path, {})
    self.assertIsNone(build_helper)

    project_definition.build_system = 'setup_py'
    build_helper = factory.BuildHelperFactory.NewBuildHelper(
        project_definition, 'source', l2tdevtools_path, {})
    self.assertIsNotNone(build_helper)

    build_helper = factory.BuildHelperFactory.NewBuildHelper(
        project_definition, 'bogus', l2tdevtools_path, {})
    self.assertIsNone(build_helper)


if __name__ == '__main__':
  unittest.main()
