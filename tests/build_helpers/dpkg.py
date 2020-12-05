#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tests for the helper for building projects from source."""

from __future__ import unicode_literals

import os
import unittest

from l2tdevtools import projects
from l2tdevtools.build_helpers import dpkg

from tests import test_lib


class DPKGBuildHelperTest(test_lib.BaseTestCase):
  """Tests for the helper to build dpkg packages (.deb)."""

  # pylint: disable=protected-access

  # TODO: add tests for _BuildPrepare
  # TODO: add tests for _BuildFinalize
  # TODO: add tests for _CheckIsInstalled
  # TODO: add tests for _CreateOriginalSourcePackage
  # TODO: add tests for _CreateOriginalSourcePackageFromZip
  # TODO: add tests for _CreatePackagingFiles
  # TODO: add tests for _GetBuildHostDistribution

  def testReadLSBReleaseConfigurationFile(self):
    """Tests the _ReadLSBReleaseConfigurationFile function."""
    test_path = self._GetTestFilePath(['lsb-release'])
    self._SkipIfPathNotExists(test_path)

    project_definition = projects.ProjectDefinition('test')

    l2tdevtools_path = os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))))

    test_build_helper = dpkg.DPKGBuildHelper(
        project_definition, l2tdevtools_path, {})
    lsb_release_values = test_build_helper._ReadLSBReleaseConfigurationFile(
        test_path)

    self.assertEqual(len(lsb_release_values), 4)

    expected_keys = [
        'distrib_codename', 'distrib_description', 'distrib_id',
        'distrib_release']

    self.assertEqual(sorted(lsb_release_values.keys()), expected_keys)

  # TODO: add tests for _RemoveOlderDPKGPackages
  # TODO: add tests for _RemoveOlderOriginalSourcePackage
  # TODO: add tests for _RemoveOlderSourceDPKGPackages

  def testRunLSBReleaseCommand(self):
    """Tests the _RunLSBReleaseCommand function."""
    project_definition = projects.ProjectDefinition('test')

    l2tdevtools_path = os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))))

    test_build_helper = dpkg.DPKGBuildHelper(
        project_definition, l2tdevtools_path, {})
    output = test_build_helper._RunLSBReleaseCommand()

    if os.path.exists('/usr/bin/lsb_release'):
      self.assertIsNotNone(output)
    else:
      self.assertIsNone(output)

  # TODO: add tests for CheckBuildDependencies


class ConfigureMakeDPKGBuildHelperTest(test_lib.BaseTestCase):
  """Tests for the helper to build dpkg packages (.deb)."""

  # TODO: add tests for Build
  # TODO: add tests for CheckBuildRequired
  # TODO: add tests for Clean


class ConfigureMakeSourceDPKGBuildHelperTest(test_lib.BaseTestCase):
  """Tests for the helper to build source dpkg packages (.deb)."""

  # TODO: add tests for Build
  # TODO: add tests for CheckBuildRequired
  # TODO: add tests for Clean


class SetupPyDPKGBuildHelperTest(test_lib.BaseTestCase):
  """Tests for the helper to build dpkg packages (.deb)."""

  # TODO: add tests for _GetFilenameSafeProjectInformation
  # TODO: add tests for Build
  # TODO: add tests for CheckBuildRequired
  # TODO: add tests for Clean


class SetupPySourceDPKGBuildHelperTest(test_lib.BaseTestCase):
  """Tests for the helper to build source dpkg packages (.deb)."""

  # TODO: add tests for _GetFilenameSafeProjectInformation
  # TODO: add tests for Build
  # TODO: add tests for CheckBuildRequired
  # TODO: add tests for Clean


if __name__ == '__main__':
  unittest.main()
