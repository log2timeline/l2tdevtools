#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tests for the dpkg build files generator."""

from __future__ import unicode_literals

import unittest

from l2tdevtools import dpkg_files
from l2tdevtools import projects

from tests import test_lib


class DPKGBuildFilesGeneratorTest(test_lib.BaseTestCase):
  """Tests for the dpkg build files generator."""

  def testGenerateChangelogFile(self):
    """Tests the _GenerateChangelogFile function."""
    project_definition = projects.ProjectDefinition('test')

    dpkg_files_generator = dpkg_files.DPKGBuildFilesGenerator(
        project_definition, '1.0', 'data_path', {})

    _ = dpkg_files_generator
    # TODO: implement tests.

  # TODO: test _GenerateCompatFile function.
  # TODO: test _GenerateControlFile function.
  # TODO: test _GenerateCopyrightFile function.
  # TODO: test _GenerateDocsFiles function.
  # TODO: test _GenerateRulesFile function.
  # TODO: test _GenerateConfigureMakeRulesFile function.
  # TODO: test _GenerateSetupPyRulesFile function.
  # TODO: test _GenerateSourceFormatFile function.
  # TODO: test GenerateFiles function.


if __name__ == '__main__':
  unittest.main()
