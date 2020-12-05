#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tests for the requirements.txt writer."""

from __future__ import unicode_literals

import unittest

from l2tdevtools import dependencies
from l2tdevtools import projects
from l2tdevtools.dependency_writers import requirements

from tests import test_lib


class RequirementsWriterTest(test_lib.BaseTestCase):
  """Tests the requirements writer."""

  def _CreateTestWriter(self):
    """Creates a dependency file writer for testing.

    Returns:
      RequirementsWriter: dependency file writer for testing.
    """
    project_definition = projects.ProjectDefinition('test')
    dependencies_file = self._GetTestFilePath(['dependencies.ini'])
    test_dependencies_file = self._GetTestFilePath(['test_dependencies.ini'])
    dependency_helper = dependencies.DependencyHelper(
        dependencies_file=dependencies_file,
        test_dependencies_file=test_dependencies_file)

    return requirements.RequirementsWriter(
        '/fake/l2tdevtools/', project_definition, dependency_helper)

  def testInitialize(self):
    """Tests the __init__ function."""
    test_writer = self._CreateTestWriter()
    self.assertIsNotNone(test_writer)

  # TODO: Add test for the Write method.


class TestRequirementsWriterTest(test_lib.BaseTestCase):
  """Tests the test requirements writer."""

  def _CreateTestWriter(self):
    """Creates a dependency file writer for testing.

    Returns:
      TestRequirementsWriter: dependency file writer for testing.
    """
    project_definition = projects.ProjectDefinition('test')
    dependencies_file = self._GetTestFilePath(['dependencies.ini'])
    test_dependencies_file = self._GetTestFilePath(['test_dependencies.ini'])
    dependency_helper = dependencies.DependencyHelper(
        dependencies_file=dependencies_file,
        test_dependencies_file=test_dependencies_file)

    return requirements.TestRequirementsWriter(
        '/fake/l2tdevtools/', project_definition, dependency_helper)

  def testInitialize(self):
    """Tests the __init__ function."""
    test_writer = self._CreateTestWriter()
    self.assertIsNotNone(test_writer)


if __name__ == '__main__':
  unittest.main()
