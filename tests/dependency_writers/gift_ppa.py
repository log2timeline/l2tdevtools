#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tests for the GIFT PPA script writer."""

from __future__ import unicode_literals

import unittest

from l2tdevtools import dependencies
from l2tdevtools.dependency_writers import gift_ppa
from l2tdevtools import projects
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

    configuration_file = self._GetTestFilePath(['dependencies.ini'])
    dependency_helper = dependencies.DependencyHelper(
        configuration_file=configuration_file)

    configuration_file = self._GetTestFilePath(['test_dependencies.ini'])
    test_dependency_helper = dependencies.DependencyHelper(
        configuration_file=configuration_file)

    return gift_ppa.GIFTPPAInstallScriptWriter(
        '/fake/l2tdevtools/', project_definition, dependency_helper,
        test_dependency_helper)

  def testFormatDPKGDebugDependencies(self):
    """Tests the _FormatDPKGDebugDependencies function."""
    test_writer = self._CreateTestWriter()

    expected_formatted_debug_dependencies = ''

    python_dependencies = test_writer._GetDPKGPythonDependencies(
        python_version=2)
    debug_dependencies = test_writer._GetDPKGDebugDependencies(
        python_dependencies, python_version=2)
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
        'PYTHON2_DEPENDENCIES="python-yaml";')

    python_dependencies = test_writer._GetDPKGPythonDependencies(
        python_version=2)
    formatted_python_dependencies = test_writer._FormatDPKGPythonDependencies(
        python_dependencies)
    self.assertEqual(
        formatted_python_dependencies, expected_formatted_python_dependencies)

  def testFormatDPKGTestDependencies(self):
    """Tests the _FormatDPKGTestDependencies function."""
    test_writer = self._CreateTestWriter()

    expected_formatted_test_dependencies = (
        'TEST_DEPENDENCIES="python-coverage\n'
        '                   python-funcsigs\n'
        '                   python-mock\n'
        '                   python-pbr\n'
        '                   python-six\n'
        '                   python-tox";')

    python_dependencies = test_writer._GetDPKGPythonDependencies(
        python_version=2)
    test_dependencies = test_writer._GetDPKGTestDependencies(
        python_dependencies, python_version=2)
    formatted_test_dependencies = test_writer._FormatDPKGTestDependencies(
        test_dependencies)
    self.assertEqual(
        formatted_test_dependencies, expected_formatted_test_dependencies)

  def testGetDPKGDebugDependencies(self):
    """Tests the _GetDPKGDebugDependencies function."""
    test_writer = self._CreateTestWriter()

    expected_debug_dependencies = []

    python_dependencies = test_writer._GetDPKGPythonDependencies(
        python_version=2)
    debug_dependencies = test_writer._GetDPKGDebugDependencies(
        python_dependencies, python_version=2)
    self.assertEqual(debug_dependencies, expected_debug_dependencies)


class GIFTPPAInstallPY2Test(test_lib.BaseTestCase):
  """Tests the GIFT PPA installation script file writer for Python 2."""

  def _CreateTestWriter(self):
    """Creates a dependency file writer for testing.

    Returns:
      GIFTPPAInstallScriptPY2Writer: dependency file writer for testing.
    """
    project_definition = projects.ProjectDefinition('test')

    configuration_file = self._GetTestFilePath(['dependencies.ini'])
    dependency_helper = dependencies.DependencyHelper(
        configuration_file=configuration_file)

    configuration_file = self._GetTestFilePath(['test_dependencies.ini'])
    test_dependency_helper = dependencies.DependencyHelper(
        configuration_file=configuration_file)

    return gift_ppa.GIFTPPAInstallScriptPY2Writer(
        '/fake/l2tdevtools/', project_definition, dependency_helper,
        test_dependency_helper)

  def testInitialize(self):
    """Tests the __init__ function."""
    test_writer = self._CreateTestWriter()
    self.assertIsNotNone(test_writer)

  # TODO: Add test for the Write method.


class GIFTPPAInstallPY3Test(test_lib.BaseTestCase):
  """Tests the GIFT PPA installation script file writer for Python 3."""

  def _CreateTestWriter(self):
    """Creates a dependency file writer for testing.

    Returns:
      GIFTPPAInstallScriptPY3Writer: dependency file writer for testing.
    """
    project_definition = projects.ProjectDefinition('test')

    configuration_file = self._GetTestFilePath(['dependencies.ini'])
    dependency_helper = dependencies.DependencyHelper(
        configuration_file=configuration_file)

    configuration_file = self._GetTestFilePath(['test_dependencies.ini'])
    test_dependency_helper = dependencies.DependencyHelper(
        configuration_file=configuration_file)

    return gift_ppa.GIFTPPAInstallScriptPY3Writer(
        '/fake/l2tdevtools/', project_definition, dependency_helper,
        test_dependency_helper)

  def testInitialize(self):
    """Tests the __init__ function."""
    test_writer = self._CreateTestWriter()
    self.assertIsNotNone(test_writer)

  # TODO: Add test for the Write method.

if __name__ == '__main__':
  unittest.main()
