#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tests for the MacOS script file writers."""

from __future__ import unicode_literals

import unittest

from l2tdevtools import dependencies
from l2tdevtools.dependency_writers import macos
from l2tdevtools.helpers import project
from tests import test_lib


class MacOSInstallScriptWriterTest(test_lib.BaseTestCase):
  """Tests the MacOS installation script file writer."""

  def testInitialize(self):
    """Tests that the writer can be initialized."""

    l2tdevtools_path = '/fake/l2tdevtools/'
    project_definition = project.ProjectHelper(l2tdevtools_path)
    configuration_file = self._GetTestFilePath(['dependencies.ini'])
    dependency_helper = dependencies.DependencyHelper(
        configuration_file=configuration_file)

    writer = macos.MacOSInstallScriptWriter(
        l2tdevtools_path, project_definition, dependency_helper)
    self.assertIsNotNone(writer)

  # TODO: Add test for the Write method.


class MacOSMakeDistScriptWriterTest(test_lib.BaseTestCase):
  """Tests the MacOS make distribution script file writer."""

  def testInitialize(self):
    """Tests that the writer can be initialized."""

    l2tdevtools_path = '/fake/l2tdevtools/'
    project_definition = project.ProjectHelper(l2tdevtools_path)
    configuration_file = self._GetTestFilePath(['dependencies.ini'])
    dependency_helper = dependencies.DependencyHelper(
        configuration_file=configuration_file)

    writer = macos.MacOSMakeDistScriptWriter(
        l2tdevtools_path, project_definition, dependency_helper)
    self.assertIsNotNone(writer)

  # TODO: Add test for the Write method.


class MacOSUninstallScriptWriterTest(test_lib.BaseTestCase):
  """Tests the MacOS uninstallation script file writer."""

  def testInitialize(self):
    """Tests that the writer can be initialized."""

    l2tdevtools_path = '/fake/l2tdevtools/'
    project_definition = project.ProjectHelper(l2tdevtools_path)
    configuration_file = self._GetTestFilePath(['dependencies.ini'])
    dependency_helper = dependencies.DependencyHelper(
        configuration_file=configuration_file)

    writer = macos.MacOSUninstallScriptWriter(
        l2tdevtools_path, project_definition, dependency_helper)
    self.assertIsNotNone(writer)

  # TODO: Add test for the Write method.


if __name__ == '__main__':
  unittest.main()
