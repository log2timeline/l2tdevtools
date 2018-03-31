#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tests for the appveyor.yml writer."""

from __future__ import unicode_literals

import unittest

from l2tdevtools import dependencies
from l2tdevtools.dependency_writers import appveyor_yml
from l2tdevtools.helpers import project
from tests import test_lib


class AppveyorYMLTest(test_lib.BaseTestCase):
  """Tests the appveyor.yml writer."""

  def testInitialize(self):
    """Tests that the writer can be initialized."""

    l2tdevtools_path = '/fake/l2tdevtools/'
    project_definition = project.ProjectHelper(l2tdevtools_path)
    configuration_file = self._GetTestFilePath(['dependencies.ini'])
    dependency_helper = dependencies.DependencyHelper(
        configuration_file=configuration_file)

    writer = appveyor_yml.AppveyorYmlWriter(
        l2tdevtools_path, project_definition, dependency_helper)
    self.assertIsNotNone(writer)

  # TODO: Add test for the Write method.


if __name__ == '__main__':
  unittest.main()
