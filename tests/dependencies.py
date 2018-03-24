#!/usr/bin/env python
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

  # pylint: disable=protected-access

  # TODO: add tests for _GetConfigValue.
  # TODO: add tests for Read.


@test_lib.skipUnlessHasTestFile(['dependencies.ini'])
class DependencyHelperTest(test_lib.BaseTestCase):
  """Tests for the dependency helper."""

  # pylint: disable=protected-access

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
        'os', module_object, '__version__', '1.0', '2.0')
    self.assertFalse(result)

    # TODO: add test with version with suffix 17.0.0b1

  def testCheckSQLite3(self):
    """Tests the _CheckSQLite3 function."""
    configuration_file = self._GetTestFilePath(['dependencies.ini'])
    dependency_helper = dependencies.DependencyHelper(
        configuration_file=configuration_file)

    dependency_helper._CheckSQLite3()

  def testImportPythonModule(self):
    """Tests the _ImportPythonModule function."""
    configuration_file = self._GetTestFilePath(['dependencies.ini'])
    dependency_helper = dependencies.DependencyHelper(
        configuration_file=configuration_file)

    module_object = dependency_helper._ImportPythonModule('os')
    self.assertIsNotNone(module_object)

    # TODO: add test with submodule.

  # TODO: add tests for _PrintCheckDependencyStatus

  def testCheckDependencies(self):
    """Tests the CheckDependencies function."""
    configuration_file = self._GetTestFilePath(['dependencies.ini'])
    dependency_helper = dependencies.DependencyHelper(
        configuration_file=configuration_file)

    dependency_helper.CheckDependencies(verbose_output=False)

  def testCheckTestDependencies(self):
    """Tests the CheckTestDependencies function."""
    configuration_file = self._GetTestFilePath(['dependencies.ini'])
    dependency_helper = dependencies.DependencyHelper(
        configuration_file=configuration_file)

    dependency_helper.CheckTestDependencies(verbose_output=False)

  def testGetDPKGDepends(self):
    """Tests the GetDPKGDepends function."""
    configuration_file = self._GetTestFilePath(['dependencies.ini'])
    dependency_helper = dependencies.DependencyHelper(
        configuration_file=configuration_file)

    dpkg_depends = dependency_helper.GetDPKGDepends()
    self.assertEqual(len(dpkg_depends), 1)

  def testGetL2TBinaries(self):
    """Tests the GetL2TBinaries function."""
    configuration_file = self._GetTestFilePath(['dependencies.ini'])
    dependency_helper = dependencies.DependencyHelper(
        configuration_file=configuration_file)

    l2tbinaries = dependency_helper.GetL2TBinaries()
    self.assertEqual(len(l2tbinaries), 1)

  def testGetInstallRequires(self):
    """Tests the GetInstallRequires function."""
    configuration_file = self._GetTestFilePath(['dependencies.ini'])
    dependency_helper = dependencies.DependencyHelper(
        configuration_file=configuration_file)

    install_requires = dependency_helper.GetInstallRequires()
    self.assertEqual(len(install_requires), 1)

  def testGetRPMRequires(self):
    """Tests the GetRPMRequires function."""
    configuration_file = self._GetTestFilePath(['dependencies.ini'])
    dependency_helper = dependencies.DependencyHelper(
        configuration_file=configuration_file)

    rpm_requires = dependency_helper.GetRPMRequires()
    self.assertEqual(len(rpm_requires), 1)


if __name__ == '__main__':
  unittest.main()
