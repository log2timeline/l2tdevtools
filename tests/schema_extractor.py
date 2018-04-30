#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tests for the SQLite database schema extractor tool."""

from __future__ import unicode_literals

import unittest

from tools import schema_extractor

from tests import test_lib


class SQLiteSchemaExtractorTest(test_lib.BaseTestCase):
  """Tests for the SQLite database file schema extractor."""

  _TEST_SCHEMA = {
      'moz_downloads': (
          'CREATE TABLE moz_downloads (id INTEGER PRIMARY KEY, name TEXT, '
          'source TEXT, target TEXT, tempPath TEXT, startTime INTEGER, endTime '
          'INTEGER, state INTEGER, referrer TEXT, entityID TEXT, currBytes '
          'INTEGER NOT NULL DEFAULT 0, maxBytes INTEGER NOT NULL DEFAULT -1, '
          'mimeType TEXT, preferredApplication TEXT, preferredAction INTEGER '
          'NOT NULL DEFAULT 0, autoResume INTEGER NOT NULL DEFAULT 0)')}

  _TEST_FORMATTED_SCHEMA = """\
      'moz_downloads': (
          'CREATE TABLE moz_downloads (id INTEGER PRIMARY KEY, name TEXT, '
          'source TEXT, target TEXT, tempPath TEXT, startTime INTEGER, '
          'endTime INTEGER, state INTEGER, referrer TEXT, entityID TEXT, '
          'currBytes INTEGER NOT NULL DEFAULT 0, maxBytes INTEGER NOT NULL '
          'DEFAULT -1, mimeType TEXT, preferredApplication TEXT, '
          'preferredAction INTEGER NOT NULL DEFAULT 0, autoResume INTEGER NOT '
          'NULL DEFAULT 0)')}]"""

  def testFormatSchema(self):
    """Tests the FormatSchema function."""
    test_extractor = schema_extractor.SQLiteSchemaExtractor()
    schema = test_extractor.FormatSchema(self._TEST_SCHEMA)

    self.assertEqual(schema, self._TEST_FORMATTED_SCHEMA)

  @test_lib.skipUnlessHasTestFile(['downloads.sqlite'])
  def testGetDatabaseSchema(self):
    """Tests the GetDatabaseSchema function."""
    test_path = self._GetTestFilePath(['downloads.sqlite'])

    test_extractor = schema_extractor.SQLiteSchemaExtractor()
    schema = test_extractor.GetDatabaseSchema(test_path)

    self.assertEqual(schema, self._TEST_SCHEMA)


if __name__ == '__main__':
  unittest.main()
