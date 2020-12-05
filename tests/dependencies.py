#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tests for the helper to check for dependencies."""

from __future__ import unicode_literals

import configparser
import io
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

  _TEST_CONFIGURATION_DATA = '\n'.join([
      '[dfdatetime]',
      'dpkg_name: python3-dfdatetime',
      'minimum_version: 20160814',
      'rpm_name: python3-dfdatetime',
      'version_property: __version__'])

  def testGetConfigValue(self):
    """Tests the _GetConfigValue function."""
    test_reader = dependencies.DependencyDefinitionReader()

    file_object = io.StringIO(self._TEST_CONFIGURATION_DATA)
    config_parser = configparser.ConfigParser(interpolation=None)
    config_parser.read_file(file_object)

    configuration_value = test_reader._GetConfigValue(
        config_parser, 'dfdatetime', 'dpkg_name')
    self.assertEqual(configuration_value, 'python3-dfdatetime')

    with self.assertRaises(configparser.NoSectionError):
      test_reader._GetConfigValue(config_parser, 'bogus', 'dpkg_name')

    configuration_value = test_reader._GetConfigValue(
        config_parser, 'dfdatetime', 'bogus')
    self.assertIsNone(configuration_value)

  def testRead(self):
    """Tests the Read function."""
    test_reader = dependencies.DependencyDefinitionReader()

    file_object = io.StringIO(self._TEST_CONFIGURATION_DATA)
    definitions = list(test_reader.Read(file_object))

    self.assertEqual(len(definitions), 1)


@test_lib.skipUnlessHasTestFile(['dependencies.ini'])
class DependencyHelperTest(test_lib.BaseTestCase):
  """Tests for the dependency helper."""

  # pylint: disable=protected-access

  def testInitialize(self):
    """Tests the __init__ function."""
    dependencies_file = self._GetTestFilePath(['dependencies.ini'])
    dependency_helper = dependencies.DependencyHelper(
        dependencies_file=dependencies_file)
    self.assertIsNotNone(dependency_helper)

    dependencies_file = self._GetTestFilePath(['bogus.ini'])
    with self.assertRaises(IOError):
      dependencies.DependencyHelper(dependencies_file=dependencies_file)

  def testCheckPythonModule(self):
    """Tests the _CheckPythonModule function."""
    dependencies_file = self._GetTestFilePath(['dependencies.ini'])
    dependency_helper = dependencies.DependencyHelper(
        dependencies_file=dependencies_file)

    dependency = dependencies.DependencyDefinition('os')
    result, _ = dependency_helper._CheckPythonModule(dependency)
    self.assertTrue(result)

    dependency = dependencies.DependencyDefinition('bogus')
    result, _ = dependency_helper._CheckPythonModule(dependency)
    self.assertFalse(result)

  def testCheckPythonModuleVersion(self):
    """Tests the _CheckPythonModuleVersion function."""
    dependencies_file = self._GetTestFilePath(['dependencies.ini'])
    dependency_helper = dependencies.DependencyHelper(
        dependencies_file=dependencies_file)

    module_object = dependency_helper._ImportPythonModule('os')

    result, _ = dependency_helper._CheckPythonModuleVersion(
        'os', module_object, '__version__', '1.0', '2.0')
    self.assertFalse(result)

    # TODO: add test with version with suffix 17.0.0b1

  def testImportPythonModule(self):
    """Tests the _ImportPythonModule function."""
    dependencies_file = self._GetTestFilePath(['dependencies.ini'])
    dependency_helper = dependencies.DependencyHelper(
        dependencies_file=dependencies_file)

    module_object = dependency_helper._ImportPythonModule('os')
    self.assertIsNotNone(module_object)

    # TODO: add test with submodule.

  # TODO: add tests for _PrintCheckDependencyStatus

  def testCheckDependencies(self):
    """Tests the CheckDependencies function."""
    dependencies_file = self._GetTestFilePath(['dependencies.ini'])
    dependency_helper = dependencies.DependencyHelper(
        dependencies_file=dependencies_file)

    dependency_helper.CheckDependencies(verbose_output=False)

  def testCheckTestDependencies(self):
    """Tests the CheckTestDependencies function."""
    dependencies_file = self._GetTestFilePath(['dependencies.ini'])
    dependency_helper = dependencies.DependencyHelper(
        dependencies_file=dependencies_file)

    dependency_helper.CheckTestDependencies(verbose_output=False)

  def testGetDPKGDepends(self):
    """Tests the GetDPKGDepends function."""
    dependencies_file = self._GetTestFilePath(['dependencies.ini'])
    dependency_helper = dependencies.DependencyHelper(
        dependencies_file=dependencies_file)

    dpkg_depends = dependency_helper.GetDPKGDepends()
    self.assertEqual(len(dpkg_depends), 1)

  def testGetL2TBinaries(self):
    """Tests the GetL2TBinaries function."""
    dependencies_file = self._GetTestFilePath(['dependencies.ini'])
    dependency_helper = dependencies.DependencyHelper(
        dependencies_file=dependencies_file)

    l2tbinaries = dependency_helper.GetL2TBinaries()
    self.assertEqual(len(l2tbinaries), 1)

  def testGetInstallRequires(self):
    """Tests the GetInstallRequires function."""
    dependencies_file = self._GetTestFilePath(['dependencies.ini'])
    dependency_helper = dependencies.DependencyHelper(
        dependencies_file=dependencies_file)

    install_requires = dependency_helper.GetInstallRequires()
    self.assertEqual(len(install_requires), 1)

  def testGetPylintRcExtensionPkgs(self):
    """Tests the GetPylintRcExtensionPkgs function."""
    dependencies_file = self._GetTestFilePath(['dependencies.ini'])
    dependency_helper = dependencies.DependencyHelper(
        dependencies_file=dependencies_file)

    extension_packages = dependency_helper.GetPylintRcExtensionPkgs()
    self.assertEqual(len(extension_packages), 0)

  def testGetRPMRequires(self):
    """Tests the GetRPMRequires function."""
    dependencies_file = self._GetTestFilePath(['dependencies.ini'])
    dependency_helper = dependencies.DependencyHelper(
        dependencies_file=dependencies_file)

    rpm_requires = dependency_helper.GetRPMRequires()
    self.assertEqual(len(rpm_requires), 1)


if __name__ == '__main__':
  unittest.main()
