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

    expected_python_dependencies = ['python-yaml']

    python_dependencies = test_writer._GetDPKGPythonDependencies(
        python_version=2)
    self.assertEqual(python_dependencies, expected_python_dependencies)

  def testGetDPKGTestDependencies(self):
    """Tests the _GetDPKGTestDependencies function."""
    test_writer = self._CreateTestWriter()

    expected_test_dependencies = [
        'python-coverage', 'python-funcsigs', 'python-mock', 'python-pbr',
        'python-six', 'tox']

    python_dependencies = test_writer._GetDPKGPythonDependencies(
        python_version=2)
    test_dependencies = test_writer._GetDPKGTestDependencies(
        python_dependencies, python_version=2)
    self.assertEqual(test_dependencies, expected_test_dependencies)

  def testGetRPMPythonDependencies(self):
    """Tests the _GetRPMPythonDependencies function."""
    test_writer = self._CreateTestWriter()

    expected_python_dependencies = ['python2-pyyaml']

    python_dependencies = test_writer._GetRPMPythonDependencies(
        python_version=2)
    self.assertEqual(python_dependencies, expected_python_dependencies)

  def testGetRPMTestDependencies(self):
    """Tests the _GetRPMTestDependencies function."""
    test_writer = self._CreateTestWriter()

    expected_test_dependencies = [
        'python2-funcsigs', 'python2-mock', 'python2-pbr', 'python2-six']

    python_dependencies = test_writer._GetRPMPythonDependencies(
        python_version=2)
    test_dependencies = test_writer._GetRPMTestDependencies(
        python_dependencies, python_version=2)
    self.assertEqual(test_dependencies, expected_test_dependencies)

  # TODO: add tests for _ReadTemplateFile.


if __name__ == '__main__':
  unittest.main()
