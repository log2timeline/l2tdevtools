#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the GIFT PPA script writer."""

import unittest

from l2tdevtools import dependencies
from l2tdevtools import projects
from l2tdevtools.dependency_writers import gift_ppa

from tests import test_lib


class GIFTPPAInstallScriptWriterTest(test_lib.BaseTestCase):
  """Tests the hared functionality for GIFT PPA installation script writer."""

  # pylint: disable=protected-access

  def _CreateTestWriter(self):
    """Creates a dependency file writer for testing.

    Returns:
      GIFTPPAInstallScriptWriter: dependency file writer for testing.
    """
    project_definition = projects.ProjectDefinition('test')
    dependencies_file = self._GetTestFilePath(['dependencies.ini'])
    test_dependencies_file = self._GetTestFilePath(['test_dependencies.ini'])
    dependency_helper = dependencies.DependencyHelper(
        dependencies_file=dependencies_file,
        test_dependencies_file=test_dependencies_file)

    return gift_ppa.GIFTPPAInstallScriptWriter(
        '/fake/l2tdevtools/', project_definition, dependency_helper)

  def testFormatDPKGDebugDependencies(self):
    """Tests the _FormatDPKGDebugDependencies function."""
    test_writer = self._CreateTestWriter()

    expected_formatted_debug_dependencies = ''

    python_dependencies = test_writer._GetDPKGPythonDependencies()
    debug_dependencies = test_writer._GetDPKGDebugDependencies(
        python_dependencies)
    formatted_debug_dependencies = test_writer._FormatDPKGDebugDependencies(
        debug_dependencies)
    self.assertEqual(
        formatted_debug_dependencies, expected_formatted_debug_dependencies)

  def testFormatDPKGDevelopmentDependencies(self):
    """Tests the _FormatDPKGDevelopmentDependencies function."""
    test_writer = self._CreateTestWriter()

    expected_formatted_development_dependencies = (
        'DEVELOPMENT_DEPENDENCIES="pylint";')

    development_dependencies = ['pylint']
    formatted_development_dependencies = (
        test_writer._FormatDPKGDevelopmentDependencies(
            development_dependencies))
    self.assertEqual(
        formatted_development_dependencies,
        expected_formatted_development_dependencies)

  def testFormatDPKGPythonDependencies(self):
    """Tests the _FormatDPKGPythonDependencies function."""
    test_writer = self._CreateTestWriter()

    expected_formatted_python_dependencies = (
        'PYTHON_DEPENDENCIES="python3-yaml";')

    python_dependencies = test_writer._GetDPKGPythonDependencies()
    formatted_python_dependencies = test_writer._FormatDPKGPythonDependencies(
        python_dependencies)
    self.assertEqual(
        formatted_python_dependencies, expected_formatted_python_dependencies)

  def testFormatDPKGTestDependencies(self):
    """Tests the _FormatDPKGTestDependencies function."""
    test_writer = self._CreateTestWriter()

    expected_formatted_test_dependencies = (
        'TEST_DEPENDENCIES="python3-mock\n'
        '                   python3-pbr\n'
        '                   python3-setuptools";')

    python_dependencies = test_writer._GetDPKGPythonDependencies()
    test_dependencies = test_writer._GetDPKGTestDependencies(
        python_dependencies)
    test_dependencies.extend(['python3-setuptools'])

    formatted_test_dependencies = test_writer._FormatDPKGTestDependencies(
        test_dependencies)
    self.assertEqual(
        formatted_test_dependencies, expected_formatted_test_dependencies)

  def testGetDPKGDebugDependencies(self):
    """Tests the _GetDPKGDebugDependencies function."""
    test_writer = self._CreateTestWriter()

    expected_debug_dependencies = []

    python_dependencies = test_writer._GetDPKGPythonDependencies()
    debug_dependencies = test_writer._GetDPKGDebugDependencies(
        python_dependencies)
    self.assertEqual(debug_dependencies, expected_debug_dependencies)

  # TODO: Add test for the Write method.


if __name__ == '__main__':
  unittest.main()
