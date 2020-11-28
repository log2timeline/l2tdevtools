#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tests for the base class for dependency file writers."""

from __future__ import unicode_literals

import unittest

from l2tdevtools import dependencies
from l2tdevtools.dependency_writers import interface
from l2tdevtools import projects
from tests import test_lib


class DependencyFileWriterTest(test_lib.BaseTestCase):
  """Tests the base class for dependency file writers."""

  # pylint: disable=protected-access

  def _CreateTestWriter(self):
    """Creates a dependency file writer for testing.

    Returns:
      DependencyFileWriter: dependency file writer for testing.
    """
    project_definition = projects.ProjectDefinition('test')

    configuration_file = self._GetTestFilePath(['dependencies.ini'])
    dependency_helper = dependencies.DependencyHelper(
        configuration_file=configuration_file)

    configuration_file = self._GetTestFilePath(['test_dependencies.ini'])
    test_dependency_helper = dependencies.DependencyHelper(
        configuration_file=configuration_file)

    return interface.DependencyFileWriter(
        '/fake/l2tdevtools/', project_definition, dependency_helper,
        test_dependency_helper)

  # TODO: add tests for _GenerateFromTemplate.

  def testGetDPKGPythonDependencies(self):
    """Tests the _GetDPKGPythonDependencies function."""
    test_writer = self._CreateTestWriter()

    expected_python_dependencies = ['python3-yaml']

    python_dependencies = test_writer._GetDPKGPythonDependencies(
        python_version=3)
    self.assertEqual(python_dependencies, expected_python_dependencies)

  def testGetDPKGTestDependencies(self):
    """Tests the _GetDPKGTestDependencies function."""
    test_writer = self._CreateTestWriter()

    expected_test_dependencies = [
        'python3-distutils', 'python3-mock', 'python3-pbr',
        'python3-setuptools', 'python3-six']

    python_dependencies = test_writer._GetDPKGPythonDependencies(
        python_version=3)
    test_dependencies = test_writer._GetDPKGTestDependencies(
        python_dependencies, python_version=3)
    self.assertEqual(test_dependencies, expected_test_dependencies)

  def testGetPyPIPythonDependencies(self):
    """Tests the _GetPyPIPythonDependencies function."""
    test_writer = self._CreateTestWriter()

    expected_python_dependencies = ['PyYAML']

    python_dependencies = test_writer._GetPyPIPythonDependencies(
        exclude_version=True)
    self.assertEqual(python_dependencies, expected_python_dependencies)

  def testGetPyPITestDependencies(self):
    """Tests the _GetPyPITestDependencies function."""
    test_writer = self._CreateTestWriter()

    expected_test_dependencies = ['mock', 'pbr', 'six']

    python_dependencies = test_writer._GetPyPIPythonDependencies(
        exclude_version=True)
    test_dependencies = test_writer._GetPyPITestDependencies(
        python_dependencies, exclude_version=True)
    self.assertEqual(test_dependencies, expected_test_dependencies)

  def testGetRPMPythonDependencies(self):
    """Tests the _GetRPMPythonDependencies function."""
    test_writer = self._CreateTestWriter()

    expected_python_dependencies = ['python3-pyyaml']

    python_dependencies = test_writer._GetRPMPythonDependencies(
        python_version=3)
    self.assertEqual(python_dependencies, expected_python_dependencies)

  def testGetRPMTestDependencies(self):
    """Tests the _GetRPMTestDependencies function."""
    test_writer = self._CreateTestWriter()

    expected_test_dependencies = [
        'python3-mock', 'python3-pbr', 'python3-setuptools', 'python3-six']

    python_dependencies = test_writer._GetRPMPythonDependencies(
        python_version=3)
    test_dependencies = test_writer._GetRPMTestDependencies(
        python_dependencies, python_version=3)
    self.assertEqual(test_dependencies, expected_test_dependencies)

  # TODO: add tests for _ReadTemplateFile.


if __name__ == '__main__':
  unittest.main()
