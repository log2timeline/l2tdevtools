#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tests for the RPM spec file generator."""

import unittest

from l2tdevtools import spec_file

from tests import test_lib


class RPMSpecFileGeneratorTest(test_lib.BaseTestCase):
  """Tests for the RPM spec file generator."""

  # pylint: disable=protected-access

  def testGetBuildDefinition(self):
    """Tests the _GetBuildDefinition function."""
    spec_file_generator = spec_file.RPMSpecFileGenerator('')

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

  def testSplitRequires(self):
    """Tests the _SplitRequires function."""
    spec_file_generator = spec_file.RPMSpecFileGenerator('')

    requires_list = spec_file_generator._SplitRequires(
        'Requires: libbde, liblnk >= 20190520')

    self.assertEqual(requires_list, ['libbde', 'liblnk >= 20190520'])

    requires_list = spec_file_generator._SplitRequires(
        'Requires: libbde liblnk >= 20190520')

    self.assertEqual(requires_list, ['libbde', 'liblnk >= 20190520'])

    requires_list = spec_file_generator._SplitRequires(
        'Requires: liblnk >= 20190520 libbde')

    self.assertEqual(requires_list, ['libbde', 'liblnk >= 20190520'])

    requires_list = spec_file_generator._SplitRequires(None)
    self.assertEqual(requires_list, [])

    with self.assertRaises(ValueError):
      spec_file_generator._SplitRequires('Bogus')

  # TODO: test RewriteSetupPyGeneratedFile function.


if __name__ == '__main__':
  unittest.main()
