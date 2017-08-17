#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the helper to check for dependencies."""

from __future__ import unicode_literals

import unittest

from l2tdevtools import dependencies

from tests import test_lib


class DependencyDefinitionTest(test_lib.BaseTestCase):
  """Tests for the dependency definition."""

  def testInitialize(self):
    """Tests the __init__ function."""
    dependency_definition = dependencies.DependencyDefinition('test')
    self.assertIsNotNone(dependency_definition)


class DependencyDefinitionReaderTest(test_lib.BaseTestCase):
  """Tests for the dependency definition reader."""

  # TODO: add tests for _GetConfigValue.
  # TODO: add tests for Read.


@test_lib.skipUnlessHasTestFile(['dependencies.ini'])
class DependencyHelperTest(test_lib.BaseTestCase):
  """Tests for the dependency helper."""

  def testInitialize(self):
    """Tests the __init__ function."""
    configuration_file = self._GetTestFilePath(['dependencies.ini'])
    dependency_helper = dependencies.DependencyHelper(
        configuration_file=configuration_file)
    self.assertIsNotNone(dependency_helper)

    with self.assertRaises(IOError):
      dependencies.DependencyHelper()

  def testCheckPythonModule(self):
    """Tests the _CheckPythonModule function."""
    configuration_file = self._GetTestFilePath(['dependencies.ini'])
    dependency_helper = dependencies.DependencyHelper(
        configuration_file=configuration_file)

    dependency = dependencies.DependencyDefinition('os')
    result, _ = dependency_helper._CheckPythonModule(dependency)
    self.assertTrue(result)

    dependency = dependencies.DependencyDefinition('bogus')
    result, _ = dependency_helper._CheckPythonModule(dependency)
    self.assertFalse(result)

  def testCheckPythonModuleVersion(self):
    """Tests the _CheckPythonModuleVersion function."""
    configuration_file = self._GetTestFilePath(['dependencies.ini'])
    dependency_helper = dependencies.DependencyHelper(
        configuration_file=configuration_file)

    module_object = dependency_helper._ImportPythonModule('os')

    result, _ = dependency_helper._CheckPythonModuleVersion(
        module_object, 'os', '__version__', '1.0', '2.0')
    self.assertFalse(result)

    # TODO: add test with version with suffix 17.0.0b1

  # TODO: add tests for _CheckSQLite3

  def testImportPythonModule(self):
    """Tests the _ImportPythonModule function."""
    configuration_file = self._GetTestFilePath(['dependencies.ini'])
    dependency_helper = dependencies.DependencyHelper(
        configuration_file=configuration_file)

    module_object = dependency_helper._ImportPythonModule('os')
    self.assertIsNotNone(module_object)

    # TODO: add test with submodule.

  # TODO: add tests for _PrintCheckDependencyStatus
  # TODO: add tests for CheckDependencies
  # TODO: add tests for CheckTestDependencies
  # TODO: add tests for GetDPKGDepends
  # TODO: add tests for GetL2TBinaries
  # TODO: add tests for GetInstallRequires
  # TODO: add tests for GetRPMRequires


if __name__ == '__main__':
  unittest.main()
