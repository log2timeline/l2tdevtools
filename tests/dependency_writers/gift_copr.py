#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tests for the GIFT COPR script writer."""

import unittest

from l2tdevtools import dependencies
from l2tdevtools import projects
from l2tdevtools.dependency_writers import gift_copr

from tests import test_lib


class GIFTCOPRInstallTest(test_lib.BaseTestCase):
  """Tests the gift_copr_install.py writer."""

  # pylint: disable=protected-access

  def _CreateTestWriter(self):
    """Creates a dependency file writer for testing.

    Returns:
      GIFTCOPRInstallScriptWriter: dependency file writer for testing.
    """
    project_definition = projects.ProjectDefinition('test')

    dependencies_file = self._GetTestFilePath(['dependencies.ini'])
    test_dependencies_file = self._GetTestFilePath(['test_dependencies.ini'])
    dependency_helper = dependencies.DependencyHelper(
        dependencies_file=dependencies_file,
        test_dependencies_file=test_dependencies_file)

    return gift_copr.GIFTCOPRInstallScriptWriter(
        '/fake/l2tdevtools/', project_definition, dependency_helper)

  def testFormatRPMDebugDependencies(self):
    """Tests the _FormatRPMDebugDependencies function."""
    test_writer = self._CreateTestWriter()

    expected_formatted_debug_dependencies = ''

    python_dependencies = test_writer._GetRPMPythonDependencies()
    debug_dependencies = test_writer._GetRPMDebugDependencies(
        python_dependencies)
    formatted_debug_dependencies = test_writer._FormatRPMDebugDependencies(
        debug_dependencies)
    self.assertEqual(
        formatted_debug_dependencies, expected_formatted_debug_dependencies)

  def testFormatRPMDevelopmentDependencies(self):
    """Tests the _FormatRPMDevelopmentDependencies function."""
    test_writer = self._CreateTestWriter()

    expected_formatted_development_dependencies = (
        'DEVELOPMENT_DEPENDENCIES="pylint";')

    development_dependencies = ['pylint']
    formatted_development_dependencies = (
        test_writer._FormatRPMDevelopmentDependencies(development_dependencies))
    self.assertEqual(
        formatted_development_dependencies,
        expected_formatted_development_dependencies)

  def testFormatRPMPythonDependencies(self):
    """Tests the _FormatRPMPythonDependencies function."""
    test_writer = self._CreateTestWriter()

    expected_formatted_python_dependencies = (
        'PYTHON3_DEPENDENCIES="python3-pyyaml";')

    python_dependencies = test_writer._GetRPMPythonDependencies()
    formatted_python_dependencies = test_writer._FormatRPMPythonDependencies(
        python_dependencies)
    self.assertEqual(
        formatted_python_dependencies, expected_formatted_python_dependencies)

  def testFormatRPMTestDependencies(self):
    """Tests the _FormatRPMTestDependencies function."""
    test_writer = self._CreateTestWriter()

    expected_formatted_test_dependencies = (
        'TEST_DEPENDENCIES="python3-mock\n'
        '                   python3-pbr\n'
        '                   python3-setuptools";')

    python_dependencies = test_writer._GetRPMPythonDependencies()
    test_dependencies = test_writer._GetRPMTestDependencies(python_dependencies)
    formatted_test_dependencies = test_writer._FormatRPMTestDependencies(
        test_dependencies)
    self.assertEqual(
        formatted_test_dependencies, expected_formatted_test_dependencies)

  def testGetRPMDebugDependencies(self):
    """Tests the _GetRPMDebugDependencies function."""
    test_writer = self._CreateTestWriter()

    expected_debug_dependencies = []

    python_dependencies = test_writer._GetRPMPythonDependencies()
    debug_dependencies = test_writer._GetRPMDebugDependencies(
        python_dependencies)
    self.assertEqual(debug_dependencies, expected_debug_dependencies)

  # TODO: Add tests for the Write method.


if __name__ == '__main__':
  unittest.main()
