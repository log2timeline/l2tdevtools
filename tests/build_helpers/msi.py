#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tests for the helper for building projects from source."""

from __future__ import unicode_literals

import os
import unittest

from l2tdevtools import projects
from l2tdevtools.build_helpers import msi

from tests import test_lib as shared_test_lib
from tests.build_helpers import test_lib


class MSIBuildHelperTest(shared_test_lib.BaseTestCase):
  """Tests for the helper to build Microsoft Installer packages (.msi)."""

  def testInitialize(self):
    """Tests the __init__ function."""
    project_definition = projects.ProjectDefinition('test')

    l2tdevtools_path = os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))))

    test_build_helper = msi.MSIBuildHelper(
        project_definition, l2tdevtools_path, {})
    self.assertIsNotNone(test_build_helper)

  # TODO: add tests for _ApplyPatches
  # TODO: add tests for _RunPreBuildScript


class ConfigureMakeMSIBuildHelperTest(shared_test_lib.BaseTestCase):
  """Tests for the helper to build Microsoft Installer packages (.msi)."""

  # TODO: add tests of __init__
  # TODO: add tests of _BuildMSBuild
  # TODO: add tests of _BuildPrepare
  # TODO: add tests of _BuildSetupPy
  # TODO: add tests of _MoveMSI
  # TODO: add tests of _SetupBuildDependencyDokan
  # TODO: add tests of _SetupBuildDependencyZeroMQ
  # TODO: add tests of _SetupBuildDependencyZlib
  # TODO: add tests of CheckBuildDependencies
  # TODO: add tests of CheckBuildRequired
  # TODO: add tests of Clean


class SetupPyMSIBuildHelperTest(shared_test_lib.BaseTestCase):
  """Tests for the helper to build Microsoft Installer packages (.msi)."""

  _TEST_PROJECT_NAME = 'dfdatetime'
  _TEST_PROJECT_VERSION = '20190517'
  _TEST_MSI_FILENAME = '{0:s}-{1:s}.1.win32.msi'.format(
      _TEST_PROJECT_NAME, _TEST_PROJECT_VERSION)

  # TODO: add tests of _GetFilenameSafeProjectInformation
  # TODO: add tests of Build

  def testCheckBuildDependencies(self):
    """Tests the CheckBuildDependencies function."""
    project_definition = projects.ProjectDefinition(self._TEST_PROJECT_NAME)
    project_definition.build_dependencies = []

    l2tdevtools_path = os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))))

    test_build_helper = msi.SetupPyMSIBuildHelper(
        project_definition, l2tdevtools_path, {})

    missing_packages = test_build_helper.CheckBuildDependencies()
    self.assertEqual(missing_packages, [])

  def testCheckBuildRequired(self):
    """Tests the CheckBuildRequired function."""
    project_definition = projects.ProjectDefinition(self._TEST_PROJECT_NAME)
    project_definition.build_dependencies = []

    l2tdevtools_path = os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))))

    test_build_helper = msi.SetupPyMSIBuildHelper(
        project_definition, l2tdevtools_path, {})

    source_helper_object = test_lib.TestSourceHelper(
        self._TEST_PROJECT_NAME, project_definition, self._TEST_PROJECT_VERSION)

    result = test_build_helper.CheckBuildRequired(source_helper_object)
    self.assertTrue(result)

  def testClean(self):
    """Tests the Clean function."""
    project_definition = projects.ProjectDefinition(self._TEST_PROJECT_NAME)
    project_definition.build_dependencies = []

    l2tdevtools_path = os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))))

    test_build_helper = msi.SetupPyMSIBuildHelper(
        project_definition, l2tdevtools_path, {})
    test_build_helper.architecture = 'win32'

    source_helper_object = test_lib.TestSourceHelper(
        self._TEST_PROJECT_NAME, project_definition, self._TEST_PROJECT_VERSION)

    with shared_test_lib.TempDirectory() as temp_directory:
      test_path = os.path.join(
          temp_directory, '{0:s}-20180101.1.win32.msi'.format(
              self._TEST_PROJECT_NAME))
      with open(test_path, 'a'):
        pass

      test_path = os.path.join(temp_directory, self._TEST_MSI_FILENAME)
      with open(test_path, 'a'):
        pass

      directory_entries = os.listdir(temp_directory)
      self.assertEqual(len(directory_entries), 2)

      current_working_directory = os.getcwd()
      os.chdir(temp_directory)

      try:
        test_build_helper.Clean(source_helper_object)
      finally:
        os.chdir(current_working_directory)

      directory_entries = os.listdir(temp_directory)
      self.assertEqual(len(directory_entries), 1)
      self.assertIn(self._TEST_MSI_FILENAME, directory_entries)


if __name__ == '__main__':
  unittest.main()
