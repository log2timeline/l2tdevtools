#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tests for the GIFT PPA script writer."""

from __future__ import unicode_literals

import unittest

from l2tdevtools import dependencies
from l2tdevtools import projects
from l2tdevtools.dependency_writers import linux_scripts

from tests import test_lib


class UbuntuInstallationScriptWriterTest(test_lib.BaseTestCase):
  """Tests the hared functionality for GIFT PPA installation script writer."""

  # pylint: disable=protected-access

  def _CreateTestWriter(self):
    """Creates a dependency file writer for testing.

    Returns:
      UbuntuInstallationScriptWriter: dependency file writer for testing.
    """
    project_definition = projects.ProjectDefinition('test')

    configuration_file = self._GetTestFilePath(['dependencies.ini'])
    dependency_helper = dependencies.DependencyHelper(
        configuration_file=configuration_file)

    configuration_file = self._GetTestFilePath(['test_dependencies.ini'])
    test_dependency_helper = dependencies.DependencyHelper(
        configuration_file=configuration_file)

    return linux_scripts.UbuntuInstallationScriptWriter(
        '/fake/l2tdevtools/', project_definition, dependency_helper,
        test_dependency_helper)

  def testFormatDPKGDebugDependencies(self):
    """Tests the _FormatDPKGDebugDependencies function."""
    test_writer = self._CreateTestWriter()

    expected_formatted_debug_dependencies = ''

    python_dependencies = test_writer._GetDPKGPythonDependencies(
        python_version=3)
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

    python_dependencies = test_writer._GetDPKGPythonDependencies(
        python_version=3)
    formatted_python_dependencies = test_writer._FormatDPKGPythonDependencies(
        python_dependencies)
    self.assertEqual(
        formatted_python_dependencies, expected_formatted_python_dependencies)

  def testFormatDPKGTestDependencies(self):
    """Tests the _FormatDPKGTestDependencies function."""
    test_writer = self._CreateTestWriter()

    expected_formatted_test_dependencies = (
        'TEST_DEPENDENCIES="python3-coverage\n'
        '                   python3-distutils\n'
        '                   python3-mock\n'
        '                   python3-pbr\n'
        '                   python3-setuptools\n'
        '                   python3-six";')

    python_dependencies = test_writer._GetDPKGPythonDependencies(
        python_version=3)
    test_dependencies = test_writer._GetDPKGTestDependencies(
        python_dependencies, python_version=3)
    formatted_test_dependencies = test_writer._FormatDPKGTestDependencies(
        test_dependencies)
    self.assertEqual(
        formatted_test_dependencies, expected_formatted_test_dependencies)

  def testGetDPKGDebugDependencies(self):
    """Tests the _GetDPKGDebugDependencies function."""
    test_writer = self._CreateTestWriter()

    expected_debug_dependencies = []

    python_dependencies = test_writer._GetDPKGPythonDependencies(
        python_version=3)
    debug_dependencies = test_writer._GetDPKGDebugDependencies(
        python_dependencies)
    self.assertEqual(debug_dependencies, expected_debug_dependencies)

  # TODO: Add test for the Write method.


if __name__ == '__main__':
  unittest.main()
