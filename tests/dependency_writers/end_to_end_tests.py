#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tests for the end-to-end tests script files writer."""

from __future__ import unicode_literals

import unittest

from l2tdevtools import dependencies
from l2tdevtools.dependency_writers import end_to_end_tests
from l2tdevtools.helpers import project
from tests import test_lib


class RunEndToEndTestsScriptWriterTest(test_lib.BaseTestCase):
  """Tests the run end-to-end test script file writer."""

  def testInitialize(self):
    """Tests the __init__ function."""
    l2tdevtools_path = '/fake/l2tdevtools/'
    project_definition = project.ProjectHelper(l2tdevtools_path)
    configuration_file = self._GetTestFilePath(['dependencies.ini'])
    dependency_helper = dependencies.DependencyHelper(
        configuration_file=configuration_file)

    writer = end_to_end_tests.RunEndToEndTestsScriptWriter(
        l2tdevtools_path, project_definition, dependency_helper, None)
    self.assertIsNotNone(writer)

  # TODO: Add test for the Write method.


if __name__ == '__main__':
  unittest.main()
