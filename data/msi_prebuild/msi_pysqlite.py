#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Pre-build script helping build pysqlite on windows."""

import io
import os
import requests
import sys
import zipfile

from distutils import msvc9compiler
from distutils.spawn import spawn

if os.name != u'nt':
  sys.exit

# This script does what's explained over there:
# https://trac.edgewall.org/wiki/PySqlite#BuildingonWindows
# To build pysqlite on windows.

# This is a dirty DIRTY hack, it so happens that this directory is in the
# library paths, because of another bug. See:
# https://github.com/ghaering/pysqlite/issues/89#issuecomment-146939384
compile_dir = u'internal'

if not os.path.isdir(compile_dir):
  os.mkdir(compile_dir)

os.chdir(compile_dir)

if not os.path.isfile(u'sqlite3.c'):
  source_directory = None
  url = u'https://www.sqlite.org/2017/sqlite-amalgamation-3190200.zip'
  request_object = requests.get(url, stream=True)
  request_object.raise_for_status()
  with zipfile.ZipFile(io.BytesIO(request_object.content)) as archive:
    for member in archive.namelist():
      member_filename = os.path.basename(member)
      if member_filename in [u'sqlite3.c', u'sqlite3.h']:
        with open(member_filename, 'wb') as expanded_file:
          expanded_file.write(archive.read(member))

compiler = msvc9compiler.MSVCCompiler()
compiler.initialize()

if not os.path.isfile(u'sqlite3.obj'):
  spawn([compiler.cc, u'-c', u'sqlite3.c'])

if not os.path.isfile(u'sqlite3.lib'):
  spawn([compiler.lib, u'sqlite3.obj', u'-out:sqlite3.lib'])
