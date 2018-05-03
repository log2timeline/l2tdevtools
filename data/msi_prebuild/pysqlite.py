#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Script to set up build environment for pysqlite on Windows.

Also see: https://trac.edgewall.org/wiki/PySqlite#BuildingonWindows
"""

from __future__ import unicode_literals

import logging
import os
import sys
import zipfile

from distutils import msvc9compiler
from distutils.spawn import spawn

# pylint: disable=import-error
# pylint: disable=no-name-in-module
if sys.version_info[0] < 3:
  # Use urllib2 here since this code should be able to be used by a default
  # Python set up.
  import urllib2 as urllib_error
  import urllib2 as urllib_request
else:
  import urllib.error as urllib_error
  import urllib.request as urllib_request


def DownloadFile(download_url):
  """Downloads a file from the URL and returns the filename.

  The filename is extracted from the last part of the URL.

  Args:
    download_url (str): URL where to download the file.

  Returns:
    str: filename if successful also if the file was already downloaded
        or None on error.
  """
  _, _, filename = download_url.rpartition('/')

  if not os.path.exists(filename):
    logging.info('Downloading: {0:s}'.format(download_url))

    try:
      url_object = urllib_request.urlopen(download_url)
    except urllib_error.URLError as exception:
      logging.warning(
          'Unable to download URL: {0:s} with error: {1:s}'.format(
              download_url, exception))
      return

    if url_object.code != 200:
      logging.warning(
          'Unable to download URL: {0:s} with status code: {1:d}'.format(
              download_url, url_object.code))
      return

    with open(filename, 'wb') as file_object:
      file_object.write(url_object.read())

  return filename


if __name__ == '__main__':
  if os.name != 'nt':
    logging.error('Unsupport operating system: {0:s}'.format(os.name))
    sys.exit(1)

  # This is a dirty DIRTY hack, it so happens that this directory is in the
  # library paths, because of another bug. See:
  # https://github.com/ghaering/pysqlite/issues/89#issuecomment-146939384
  compile_dir = 'internal'

  if not os.path.isdir(compile_dir):
    os.mkdir(compile_dir)

  os.chdir(compile_dir)

  if not os.path.isfile('sqlite3.c'):
    url = 'https://www.sqlite.org/2018/sqlite-amalgamation-3230100.zip'

    sqlite_filename = DownloadFile(url)
    if not sqlite_filename:
      logging.error('Unable to download: sqlite-amalgamation.')
      sys.exit(1)

    with zipfile.ZipFile(sqlite_filename) as archive:
      for member in archive.namelist():
        member_filename = os.path.basename(member)
        if member_filename in ('sqlite3.c', 'sqlite3.h'):
          with open(member_filename, 'wb') as expanded_file:
            expanded_file.write(archive.read(member))

  compiler = msvc9compiler.MSVCCompiler()
  compiler.initialize()

  if not os.path.isfile('sqlite3.obj'):
    spawn([compiler.cc, '-c', 'sqlite3.c'])

  if not os.path.isfile('sqlite3.lib'):
    spawn([compiler.lib, 'sqlite3.obj', '-out:sqlite3.lib'])

  sys.exit(0)
