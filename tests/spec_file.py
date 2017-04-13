#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the RPM spec file generator."""

import unittest

from l2tdevtools import spec_file


class RPMSpecFileGeneratorTest(unittest.TestCase):
  """Tests for the RPM spec file generator."""

  def testGetBuildDefinition(self):
    """Tests the _GetBuildDefinition function."""
    spec_file_generator = spec_file.RPMSpecFileGenerator()

    _ = spec_file_generator
    # TODO: implement tests.

  # TODO: test _GetDocumentationFilesDefinition function.
  # TODO: test _GetInstallDefinition function.
  # TODO: test _GetLicenseFileDefinition function.
  # TODO: test _WriteChangeLog function.
  # TODO: test _WritePython2PackageDefinition function.
  # TODO: test _WritePython2PackageFiles function.
  # TODO: test _WritePython3PackageDefinition function.
  # TODO: test _WritePython3PackageFiles function.
  # TODO: test GenerateWithSetupPy function.
  # TODO: test _RewriteSetupPyGeneratedFile function.
  # TODO: test RewriteSetupPyGeneratedFile function.
  # TODO: test RewriteSetupPyGeneratedFileForOSC function.


if __name__ == '__main__':
  unittest.main()
