#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the project object implementations."""

import os
import unittest

from l2tdevtools import projects


class ProjectDefinitionReaderTest(unittest.TestCase):
  """Tests for the project definition reader."""

  def testDownloadPageContent(self):
    """Tests the DownloadPageContent functions."""
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
