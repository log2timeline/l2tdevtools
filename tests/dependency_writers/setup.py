#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the setup configuration and script file writers."""

import unittest

from l2tdevtools import dependencies
from l2tdevtools.dependency_writers import setup
from l2tdevtools.helpers import project
from tests import test_lib


class PyprojectTomlWriterTest(test_lib.BaseTestCase):
  """Tests the pyproject.toml configuration file writer."""

  def testInitialize(self):
    """Tests that the writer can be initialized."""
    l2tdevtools_path = '/fake/l2tdevtools/'
    project_definition = project.ProjectHelper(l2tdevtools_path)
    dependencies_file = self._GetTestFilePath(['dependencies.ini'])
    test_dependencies_file = self._GetTestFilePath(['test_dependencies.ini'])
    dependency_helper = dependencies.DependencyHelper(
        dependencies_file=dependencies_file,
        test_dependencies_file=test_dependencies_file)

    writer = setup.PyprojectTomlWriter(
        l2tdevtools_path, project_definition, dependency_helper)
    self.assertIsNotNone(writer)

  # TODO: Add test for the Write method.


if __name__ == '__main__':
  unittest.main()
