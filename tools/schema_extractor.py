#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Script to extract the database schema from SQLite database files."""

from __future__ import print_function
from __future__ import unicode_literals

import argparse
import logging
import os
import sys
import textwrap

try:
  import pyperclip
except ImportError:
  pyperclip = None

# pylint: disable=wrong-import-order
try:
  from pysqlite2 import dbapi2 as sqlite3
except ImportError:
  import sqlite3


class SQLiteSchemaExtractor(object):
  """SQLite database file schema extractor."""

  _SCHEMA_QUERY = (
      'SELECT tbl_name, sql '
      'FROM sqlite_master '
      'WHERE type = "table" AND tbl_name != "xp_proc" '
      'AND tbl_name != "sqlite_sequence"')

  def FormatSchema(self, schema):
    """Formats a schema into a word-wrapped string.

    Args:
      schema (dict[str, str]): schema as an SQL query per table name.

    Returns:
      str: schema formatted as word-wrapped string.
    """
    textwrapper = textwrap.TextWrapper()
    textwrapper.break_long_words = False
    textwrapper.drop_whitespace = True
    textwrapper.width = 80 - (10 + 4)

    lines = []
    table_index = 1
    number_of_tables = len(schema)
    for table_name, query in sorted(schema.items()):
      line = '      \'{0:s}\': ('.format(table_name)
      lines.append(line)

      query = query.replace('\'', '\\\'')
      query = textwrapper.wrap(query)
      query = ['{0:s}\'{1:s} \''.format(' ' * 10, line) for line in query]

      if table_index == number_of_tables:
        query[-1] = '{0:s}\')}}]'.format(query[-1][:-2])
      else:
        query[-1] = '{0:s}\'),'.format(query[-1][:-2])

      lines.extend(query)
      table_index += 1

    return '\n'.join(lines)

  def GetDatabaseSchema(self, database_path):
    """Retrieves schema from given database.

    Args:
      database_path (str): file path to database.

    Returns:
      dict[str, str]: schema as an SQL query per table name or None if
          the schema could not be retrieved.
    """
    schema = None

    database = sqlite3.connect(database_path)
    database.row_factory = sqlite3.Row

    try:
      cursor = database.cursor()

      rows = cursor.execute(self._SCHEMA_QUERY)

      schema = {
          table_name: ' '.join(query.split()) for table_name, query in rows}

    except sqlite3.DatabaseError as exception:
      logging.error('Unable to query schema with error: {0!s}'.format(
          exception))

    finally:
      database.close()

    return schema


def Main():
  """The main program function.

  Returns:
    bool: True if successful or False if not.
  """
  argument_parser = argparse.ArgumentParser(description=(
      'Extract the database schema from a SQLite database file.'))

  if pyperclip:
    argument_parser.add_argument(
        '--to-clipboard', '--to_clipboard', dest='to_clipboard',
        action='store_true', default=False, help=(
            'copy the database schema to the clipboard instead of writing '
            'to stdout.'))

  argument_parser.add_argument(
      'database_path', type=str,
      help='path to the database file to extract schema from.')

  options = argument_parser.parse_args()

  if not os.path.exists(options.database_path):
    print('No such database file: {0:s}'.format(options.database_path))
    return False

  extractor = SQLiteSchemaExtractor()

  database_schema = extractor.GetDatabaseSchema(options.database_path)
  if not database_schema:
    print('Unable to determine schema from database file: {0:s}'.format(
        options.database_path))
    return False

  database_schema = extractor.FormatSchema(database_schema)

  if pyperclip and options.to_clipboard:
    pyperclip.copy(database_schema)
  else:
    print(database_schema)

  return True


if __name__ == '__main__':
  if not Main():
    sys.exit(1)
  else:
    sys.exit(0)
