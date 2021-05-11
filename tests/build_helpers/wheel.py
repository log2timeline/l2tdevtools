#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tests for the helper for building projects from source."""

import os
import shutil
import unittest

from l2tdevtools import projects
from l2tdevtools.build_helpers import wheel

from tests import test_lib as shared_test_lib
from tests.build_helpers import test_lib


class WheelBuildHelperTest(shared_test_lib.BaseTestCase):
  """Tests for the helper to build Python wheel packages (.whl)."""

  # pylint: disable=protected-access

  _TEST_PROJECT_NAME = 'dfdatetime'
  _TEST_PROJECT_VERSION = '20190517'
  _TEST_WHEEL_FILENAME = '{0:s}-{1:s}-py2.py3-none-any.whl'.format(
      _TEST_PROJECT_NAME, _TEST_PROJECT_VERSION)

  def testInitialize(self):
    """Tests the __init__ function."""
    project_definition = projects.ProjectDefinition('test')

    l2tdevtools_path = os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))))

    test_build_helper = wheel.WheelBuildHelper(
        project_definition, l2tdevtools_path, {})
    self.assertIsNotNone(test_build_helper)

  def testGetWheelFilenameProjectInformation(self):
    """Tests the _GetWheelFilenameProjectInformation function."""
    project_definition = projects.ProjectDefinition(self._TEST_PROJECT_NAME)

    l2tdevtools_path = os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))))

    test_build_helper = wheel.SetupPyWheelBuildHelper(
        project_definition, l2tdevtools_path, {})

    source_helper_object = test_lib.TestSourceHelper(
        self._TEST_PROJECT_NAME, project_definition, self._TEST_PROJECT_VERSION)

    project_name, project_version = (
        test_build_helper._GetWheelFilenameProjectInformation(
            source_helper_object))
    self.assertEqual(project_name, self._TEST_PROJECT_NAME)
    self.assertEqual(project_version, self._TEST_PROJECT_VERSION)

  # TODO: add tests for _MoveWheel

  def testCheckBuildDependencies(self):
    """Tests the CheckBuildDependencies function."""
    project_definition = projects.ProjectDefinition(self._TEST_PROJECT_NAME)
    project_definition.build_dependencies = []

    l2tdevtools_path = os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))))

    test_build_helper = wheel.SetupPyWheelBuildHelper(
        project_definition, l2tdevtools_path, {})

    missing_packages = test_build_helper.CheckBuildDependencies()
    self.assertEqual(missing_packages, [])

  def testCheckBuildRequired(self):
    """Tests the CheckBuildRequired function."""
    project_definition = projects.ProjectDefinition(self._TEST_PROJECT_NAME)
    project_definition.build_dependencies = []

    l2tdevtools_path = os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))))

    test_build_helper = wheel.SetupPyWheelBuildHelper(
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

    test_build_helper = wheel.SetupPyWheelBuildHelper(
        project_definition, l2tdevtools_path, {})

    source_helper_object = test_lib.TestSourceHelper(
        self._TEST_PROJECT_NAME, project_definition, self._TEST_PROJECT_VERSION)

    with shared_test_lib.TempDirectory() as temp_directory:
      test_path = os.path.join(
          temp_directory, '{0:s}-20180101-py2.py3-none-any.whl'.format(
              self._TEST_PROJECT_NAME))
      with open(test_path, 'a'):
        pass

      test_path = os.path.join(temp_directory, self._TEST_WHEEL_FILENAME)
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
      self.assertIn(self._TEST_WHEEL_FILENAME, directory_entries)


class ConfigureMakeWheelBuildHelperTest(shared_test_lib.BaseTestCase):
  """Tests for the helper to build Python wheel packages (.whl)."""

  _TEST_PROJECT_NAME = 'libsigscan'
  _TEST_PROJECT_VERSION = '20191006'
  _TEST_SOURCE_PACKAGE = '{0:s}-{1:s}.tar.gz'.format(
      _TEST_PROJECT_NAME, _TEST_PROJECT_VERSION)

  def testBuild(self):
    """Tests the Build function."""
    project_definition = projects.ProjectDefinition(self._TEST_PROJECT_NAME)
    project_definition.build_dependencies = []
    project_definition.wheel_name = 'libsigscan_python'

    l2tdevtools_path = os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))))

    test_build_helper = wheel.SetupPyWheelBuildHelper(
        project_definition, l2tdevtools_path, {})

    source_helper_object = test_lib.TestSourceHelper(
        self._TEST_PROJECT_NAME, project_definition, self._TEST_PROJECT_VERSION)

    with shared_test_lib.TempDirectory() as temp_directory:
      test_path = os.path.join(
          l2tdevtools_path, 'test_data', self._TEST_SOURCE_PACKAGE)
      shutil.copy(test_path, temp_directory)

      directory_entries = os.listdir(temp_directory)
      self.assertEqual(len(directory_entries), 1)

      current_working_directory = os.getcwd()
      os.chdir(temp_directory)

      try:
        source_helper_object.Create()
        test_build_helper.Build(source_helper_object)
      finally:
        os.chdir(current_working_directory)

      directory_entries = os.listdir(temp_directory)
      self.assertIn('build.log', directory_entries)

      if len(directory_entries) < 4:
        build_log_path = os.path.join(temp_directory, 'build.log')
        with open(build_log_path, 'rt') as file_object:
          print(''.join(file_object.readlines()))

      self.assertEqual(len(directory_entries), 4)


class SetupPyWheelBuildHelperTest(shared_test_lib.BaseTestCase):
  """Tests for the helper to build Python wheel packages (.whl)."""

  _TEST_PROJECT_NAME = 'dfdatetime'
  _TEST_PROJECT_VERSION = '20190517'
  _TEST_SOURCE_PACKAGE = '{0:s}-{1:s}.tar.gz'.format(
      _TEST_PROJECT_NAME, _TEST_PROJECT_VERSION)
  _TEST_WHEEL_FILENAME = '{0:s}-{1:s}-py2.py3-none-any.whl'.format(
      _TEST_PROJECT_NAME, _TEST_PROJECT_VERSION)

  def testBuild(self):
    """Tests the Build function."""
    project_definition = projects.ProjectDefinition(self._TEST_PROJECT_NAME)
    project_definition.build_dependencies = []

    l2tdevtools_path = os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))))

    test_build_helper = wheel.SetupPyWheelBuildHelper(
        project_definition, l2tdevtools_path, {})

    source_helper_object = test_lib.TestSourceHelper(
        self._TEST_PROJECT_NAME, project_definition, self._TEST_PROJECT_VERSION)

    with shared_test_lib.TempDirectory() as temp_directory:
      test_path = os.path.join(
          l2tdevtools_path, 'test_data', self._TEST_SOURCE_PACKAGE)
      shutil.copy(test_path, temp_directory)

      directory_entries = os.listdir(temp_directory)
      self.assertEqual(len(directory_entries), 1)

      current_working_directory = os.getcwd()
      os.chdir(temp_directory)

      try:
        source_helper_object.Create()
        test_build_helper.Build(source_helper_object)
      finally:
        os.chdir(current_working_directory)

      directory_entries = os.listdir(temp_directory)
      self.assertIn('build.log', directory_entries)

      if len(directory_entries) < 4:
        build_log_path = os.path.join(temp_directory, 'build.log')
        with open(build_log_path, 'rt') as file_object:
          print(''.join(file_object.readlines()))

      self.assertEqual(len(directory_entries), 4)
      self.assertIn(self._TEST_WHEEL_FILENAME, directory_entries)


if __name__ == '__main__':
  unittest.main()
