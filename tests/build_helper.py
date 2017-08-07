#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the helper for building projects from source."""

from __future__ import unicode_literals

import unittest

from l2tdevtools import build_helper
from l2tdevtools import projects


class BuildHelperTest(unittest.TestCase):
  """Tests for the helper to build projects from source."""

  def testCheckBuildDependencies(self):
    """Tests the CheckBuildDependencies function."""
    project_definition = projects.ProjectDefinition('test')
    build_helper_object = build_helper.BuildHelper(project_definition, '')

    build_dependencies = build_helper_object.CheckBuildDependencies()
    self.assertEqual(build_dependencies, [])

  def testCheckBuildRequired(self):
    """Tests the CheckBuildRequired function."""
    project_definition = projects.ProjectDefinition('test')
    build_helper_object = build_helper.BuildHelper(project_definition, '')

    result = build_helper_object.CheckBuildRequired(None)
    self.assertTrue(result)


class DPKGBuildHelperTest(unittest.TestCase):
  """Tests for the helper to build dpkg packages (.deb)."""

  # TODO: add tests.


class ConfigureMakeDPKGBuildHelperTest(unittest.TestCase):
  """Tests for the helper to build dpkg packages (.deb)."""

  # TODO: add tests.


class ConfigureMakeSourceDPKGBuildHelperTest(unittest.TestCase):
  """Tests for the helper to build source dpkg packages (.deb)."""

  # TODO: add tests.


class SetupPyDPKGBuildHelperTest(unittest.TestCase):
  """Tests for the helper to build dpkg packages (.deb)."""

  # TODO: add tests.


class SetupPySourceDPKGBuildHelperTest(unittest.TestCase):
  """Tests for the helper to build source dpkg packages (.deb)."""

  # TODO: add tests.


class MSIBuildHelperTest(unittest.TestCase):
  """Tests for the helper to build Microsoft Installer packages (.msi)."""

  # TODO: add tests.


class ConfigureMakeMSIBuildHelperTest(unittest.TestCase):
  """Tests for the helper to build Microsoft Installer packages (.msi)."""

  # TODO: add tests.


class SetupPyMSIBuildHelperTest(unittest.TestCase):
  """Tests for the helper to build Microsoft Installer packages (.msi)."""

  # TODO: add tests.


class OSCBuildHelperTest(unittest.TestCase):
  """Tests for the build with osc for the openSUSE build service."""

  # TODO: add tests.


class ConfigureMakeOSCBuildHelperTest(unittest.TestCase):
  """Tests for the build with osc for the openSUSE build service."""

  # TODO: add tests.


class SetupPyOSCBuildHelperTest(unittest.TestCase):
  """Tests for the build with osc for the openSUSE build service."""

  # TODO: add tests.

# TODO: add PKGBuildHelper tests.
# TODO: add ConfigureMakePKGBuildHelper tests.
# TODO: add SetupPyPKGBuildHelper tests.

# TODO: add BaseRPMBuildHelper tests.
# TODO: add RPMBuildHelper tests.
# TODO: add ConfigureMakeRPMBuildHelper tests.
# TODO: add SetupPyRPMBuildHelper tests.

# TODO: add SRPMBuildHelper tests.
# TODO: add ConfigureMakeSRPMBuildHelper tests.
# TODO: add SetupPySRPMBuildHelper tests.

# TODO: add SourceBuildHelper tests.
# TODO: add ConfigureMakeSourceBuildHelper tests.
# TODO: add SetupPySourceBuildHelper tests.

# TODO: add BuildHelperFactory tests.


if __name__ == '__main__':
  unittest.main()
