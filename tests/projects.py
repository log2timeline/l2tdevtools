#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the project definitions."""

import os
import unittest

from l2tdevtools import projects


class ProjectDefinitionTest(unittest.TestCase):
  """Tests for the project definition."""

  def testIsPython2Only(self):
    """Tests the IsPython2Only function."""
    project_definition = projects.ProjectDefinition(u'test')

    result = project_definition.IsPython2Only()
    self.assertFalse(result)


class ProjectVersionDefinitionTest(unittest.TestCase):
  """Tests for the project version definition."""

  def testInitialize(self):
    """Tests the __init__ function."""
    project_version_definition = projects.ProjectVersionDefinition(u'')
    self.assertIsNotNone(project_version_definition)

    project_version_definition = projects.ProjectVersionDefinition(u'>1.0')
    self.assertIsNotNone(project_version_definition)

    project_version_definition = projects.ProjectVersionDefinition(u'<=1.0')
    self.assertIsNotNone(project_version_definition)

    project_version_definition = projects.ProjectVersionDefinition(
        u'>=1.0,<2.0')
    self.assertIsNotNone(project_version_definition)

    project_version_definition = projects.ProjectVersionDefinition(
        u'>=1.0,==2.0')
    self.assertIsNotNone(project_version_definition)

    project_version_definition = projects.ProjectVersionDefinition(
        u'>=1.0,<2.0,>3.0')
    self.assertIsNotNone(project_version_definition)

    project_version_definition = projects.ProjectVersionDefinition(u'bogus')
    self.assertIsNotNone(project_version_definition)

  def testVersionStringAttribute(self):
    """Tests the version_string attribute."""
    project_version_definition = projects.ProjectVersionDefinition(u'>1.0')
    self.assertIsNotNone(project_version_definition)

    self.assertEqual(project_version_definition.version_string, u'>1.0')

  def testGetEarliestVersion(self):
    """Tests the GetEarliestVersion function."""
    project_version_definition = projects.ProjectVersionDefinition(u'>1.0')
    self.assertIsNotNone(project_version_definition)

    earliest_version = project_version_definition.GetEarliestVersion()
    self.assertEqual(earliest_version, [u'>', u'1', u'0'])


class ProjectDefinitionReaderTest(unittest.TestCase):
  """Tests for the project definition reader."""

  # TODO: test _GetConfigValue function.

  def testRead(self):
    """Tests the Read function."""
    config_file = os.path.join(u'data', u'projects.ini')

    project_definitions = {}
    with open(config_file) as file_object:
      project_definition_reader = projects.ProjectDefinitionReader()
      for project_definition in project_definition_reader.Read(
          file_object):
        project_definitions[project_definition.name] = (
            project_definition)

    self.assertGreaterEqual(len(project_definitions), 1)

    project_definition = project_definitions[u'artifacts']

    self.assertEqual(project_definition.name, u'artifacts')
    self.assertIsNotNone(project_definition.version)

    self.assertEqual(
        project_definition.version.version_string, u'>=20150409')

    expected_download_url = (
        u'https://github.com/ForensicArtifacts/artifacts/releases')
    self.assertEqual(project_definition.download_url, expected_download_url)


if __name__ == '__main__':
  unittest.main()
