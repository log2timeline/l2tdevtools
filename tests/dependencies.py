#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the dependencies object implementations."""

import os
import unittest

from l2tdevtools import dependencies


class DependencyDefinitionReaderTest(unittest.TestCase):
  """Tests for the dependency definition reader."""

  def testDownloadPageContent(self):
    """Tests the DownloadPageContent functions."""
    config_file = os.path.join(u'data', u'projects.ini')

    dependency_definitions = {}
    with open(config_file) as file_object:
      dependency_definition_reader = dependencies.DependencyDefinitionReader()
      for dependency_definition in dependency_definition_reader.Read(
          file_object):
        dependency_definitions[dependency_definition.name] = (
            dependency_definition)

    self.assertGreaterEqual(len(dependency_definitions), 1)

    dependency_definition = dependency_definitions[u'artifacts']

    self.assertEqual(dependency_definition.name, u'artifacts')
    self.assertIsNotNone(dependency_definition.version)

    self.assertEqual(
        dependency_definition.version.version_string, u'>=20150409')

    expected_download_url = (
        u'https://github.com/ForensicArtifacts/artifacts/releases')
    self.assertEqual(dependency_definition.download_url, expected_download_url)


if __name__ == '__main__':
  unittest.main()
