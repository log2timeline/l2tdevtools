#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the dpkg build files generator."""

import unittest

from l2tdevtools import dpkg_files


class DPKGBuildFilesGeneratorTest(unittest.TestCase):
  """Tests for the dpkg build files generator."""

  def testGenerateChangelogFile(self):
    """Tests the _GenerateChangelogFile function."""
    dpkg_files_generator = dpkg_files.DPKGBuildFilesGenerator(
        u'test', u'1.0', None, u'')

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
  # TODO: test _IsPython2Only function.
  # TODO: test GenerateFiles function.


if __name__ == '__main__':
  unittest.main()
