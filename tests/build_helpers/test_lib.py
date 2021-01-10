# -*- coding: utf-8 -*-
"""Build helper related functions and classes for testing."""

import logging
import os
import tarfile

from l2tdevtools import source_helper


class TestSourceHelper(source_helper.SourceHelper):
  """Test helper to manage project source code."""

  def __init__(self, project_name, project_definition, project_version):
    """Initializes a source helper.

    Args:
      project_name (str): name of the project.
      project_definition (ProjectDefinition): project definition.
      project_version (str): version of the project source code.
    """
    super(TestSourceHelper, self).__init__(project_name, project_definition)
    self._project_version = project_version
    self._source_directory_path = '{0:s}-{1:s}'.format(
        project_name, project_version)
    self._source_package_filename = '{0:s}-{1:s}.tar.gz'.format(
        project_name, project_version)

  # pylint: disable=redundant-returns-doc

  def _CreateFromTar(self, source_filename):
    """Creates the source directory from a .tar source package.

    Args:
      source_filename (str): filename of the source package.

    Returns:
      str: name of the source directory or None if no files can be extracted
          from the .tar.gz source package.
    """
    archive = tarfile.open(source_filename, 'r:*', encoding='utf-8')
    directory_name = ''

    for tar_info in archive.getmembers():
      filename = getattr(tar_info, 'name', None)

      if isinstance(filename, bytes):
        try:
          filename = filename.decode('utf8')
        except UnicodeDecodeError:
          logging.warning(
              'Unable to decode filename in tar file: {0:s}'.format(
                  source_filename))
          continue

      if filename is None:
        logging.warning('Missing filename in tar file: {0:s}'.format(
            source_filename))
        continue

      if not directory_name:
        # Note that this will set directory name to an empty string
        # if filename start with a /.
        directory_name, _, _ = filename.partition('/')
        if not directory_name or directory_name.startswith('..'):
          logging.error(
              'Unsupported directory name in tar file: {0:s}'.format(
                  source_filename))
          return None
        if os.path.exists(directory_name):
          break
        logging.info('Extracting: {0:s}'.format(source_filename))

      elif not filename.startswith(directory_name):
        logging.warning(
            'Skipping: {0:s} in tar file: {1:s}'.format(
                filename, source_filename))
        continue

      archive.extract(tar_info)
    archive.close()

    return directory_name

  def Create(self):
    """Creates the source directory.

    Returns:
      str: name of the source directory or None on error.
    """
    # TODO: use shutil.unpack_archive(test_path, temp_directory) when Python 2
    # support has been removed.

    return self._CreateFromTar(self._source_package_filename)

  def GetProjectIdentifier(self):
    """Retrieves the project identifier for a given project name.

    Returns:
      str: project identifier or None on error.
    """
    return 'com.github.log2timeline.{0:s}'.format(self.project_name)

  def GetProjectVersion(self):
    """Retrieves the version number for a given project name.

    Returns:
      str: version number or None on error.
    """
    return self._project_version

  def GetSourceDirectoryPath(self):
    """Retrieves the path of the source directory.

    Returns:
      str: path of the source directory or None if not available.
    """
    return self._source_directory_path

  def GetSourcePackageFilename(self):
    """Retrieves the filename of the source package.

    This function downloads the source package if not done so previously.

    Returns:
      str: filename of the source package or None if not available.
    """
    return self._source_package_filename
