# -*- coding: utf-8 -*-
"""Helper for managing project source code."""

from __future__ import unicode_literals

import abc
import glob
import logging
import os
import re
import shutil
import subprocess
import tarfile
import zipfile

from l2tdevtools import py2to3


class SourceHelper(object):
  """Helper to manager project source code."""

  def __init__(self, project_name, project_definition):
    """Initializes a source helper.

    Args:
      project_name (str): name of the project.
      project_definition (ProjectDefinition): project definition.
    """
    super(SourceHelper, self).__init__()
    self._project_definition = project_definition
    self.project_name = project_name

  @abc.abstractmethod
  def Create(self):
    """Creates the source directory.

    Returns:
      str: name of the source directory or None on error.
    """

  @abc.abstractmethod
  def GetProjectIdentifier(self):
    """Retrieves the project identifier for a given project name.

    Returns:
      str: project identifier or None on error.
    """


class GitRepositorySourceHelper(SourceHelper):
  """Class that manages the source code from a git repository."""

  def __init__(self, project_name, project_definition):
    """Initializes a source helper.

    Args:
      project_name (str): name of the project.
      project_definition (ProjectDefinition): project definition.
    """
    super(GitRepositorySourceHelper, self).__init__(
        project_name, project_definition)
    self._git_url = project_definition.git_url

  def Clean(self):
    """Removes a previous version of the source directory."""
    if os.path.exists(self.project_name):
      logging.info('Removing: {0:s}'.format(self.project_name))
      shutil.rmtree(self.project_name)

  def Create(self):
    """Creates the source directory from the git repository.

    Returns:
      str: name of the source directory or None on error.
    """
    if not self.project_name or not self._git_url:
      return None

    command = 'git clone {0:s}'.format(self._git_url)
    exit_code = subprocess.call(
        '{0:s}'.format(command), shell=True)
    if exit_code != 0:
      logging.error('Running: "{0:s}" failed.'.format(command))
      return None

    return self.project_name

  def GetProjectIdentifier(self):
    """Retrieves the project identifier for a given project name.

    Returns:
      str: project identifier or None on error.
    """
    # TODO: determine project identifier based on git url.
    return None


class LibyalGitRepositorySourceHelper(GitRepositorySourceHelper):
  """Class that manages the source code from a libyal git repository."""

  def Create(self):
    """Creates the source directory from the git repository.

    Returns:
      str: name of the source directory or None on error.
    """
    if not self.project_name or not self._git_url:
      return None

    command = 'git clone {0:s}'.format(self._git_url)
    exit_code = subprocess.call(
        '{0:s}'.format(command), shell=True)
    if exit_code != 0:
      logging.error('Running: "{0:s}" failed.'.format(command))
      return None

    source_directory = self.project_name

    command = './synclibs.sh'
    exit_code = subprocess.call(
        '(cd {0:s} && {1:s})'.format(source_directory, command), shell=True)
    if exit_code != 0:
      logging.error('Running: "{0:s}" failed.'.format(command))
      return None

    command = './autogen.sh'
    exit_code = subprocess.call(
        '(cd {0:s} && {1:s})'.format(source_directory, command), shell=True)
    if exit_code != 0:
      logging.error('Running: "{0:s}" failed.'.format(command))
      return None

    command = './configure'
    exit_code = subprocess.call(
        '(cd {0:s} && {1:s})'.format(source_directory, command), shell=True)
    if exit_code != 0:
      logging.error('Running: "{0:s}" failed.'.format(command))
      return None

    return source_directory


class SourcePackageHelper(SourceHelper):
  """Class that manages the source code from a source package."""

  ENCODING = 'utf-8'

  def __init__(self, project_name, project_definition, download_helper_object):
    """Initializes a source package helper.

    Args:
      project_name (str): name of the project.
      project_definition (ProjectDefinition): project definition.
      download_helper_object (DownloadHelper): download helper.
    """
    super(SourcePackageHelper, self).__init__(project_name, project_definition)
    self._download_helper = download_helper_object
    self._project_version = None
    self._source_filename = None

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

      if isinstance(filename, py2to3.BYTES_TYPE):
        try:
          filename = filename.decode(self.ENCODING)
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

  def _CreateFromZip(self, source_filename):
    """Creates the source directory from a .zip source package.

    Args:
      source_filename (str): filename of the source package.

    Returns:
      str: name of the source directory or None if no files can be extracted
          from the .zip source package.
    """
    archive = zipfile.ZipFile(source_filename, 'r')
    directory_name = ''

    for zip_info in archive.infolist():
      filename = getattr(zip_info, 'filename', None)
      if filename is None:
        logging.warning('Missing filename in zip file: {0:s}'.format(
            source_filename))
        continue

      if not directory_name:
        # Note that this will set directory name to an empty string
        # if filename start with a /.
        directory_name, _, _ = filename.partition('/')
        if not directory_name or directory_name.startswith('..'):
          logging.error(
              'Unsupported directory name in zip file: {0:s}'.format(
                  source_filename))
          return None

        if os.path.exists(directory_name):
          break

        logging.info('Extracting: {0:s}'.format(source_filename))

      elif not filename.startswith(directory_name):
        logging.warning(
            'Skipping: {0:s} in zip file: {1:s}'.format(
                filename, source_filename))
        continue

      archive.extract(zip_info)
    archive.close()

    return directory_name

  def Clean(self):
    """Removes previous versions of source packages and directories."""
    project_version = self.GetProjectVersion()
    if not project_version:
      return

    filenames_to_ignore = re.compile(
        '^{0:s}-.*{1!s}'.format(self.project_name, project_version))

    # Remove previous versions of source packages in the format:
    # project-*.tar.gz
    filenames = glob.glob('{0:s}-*.tar.gz'.format(self.project_name))
    for filename in filenames:
      if not filenames_to_ignore.match(filename):
        logging.info('Removing: {0:s}'.format(filename))
        os.remove(filename)

    # Remove previous versions of source packages in the format:
    # project-*.tgz
    filenames = glob.glob('{0:s}-*.tgz'.format(self.project_name))
    for filename in filenames:
      if not filenames_to_ignore.match(filename):
        logging.info('Removing: {0:s}'.format(filename))
        os.remove(filename)

    # Remove previous versions of source packages in the format:
    # project-*.zip
    filenames = glob.glob('{0:s}-*.zip'.format(self.project_name))
    for filename in filenames:
      if not filenames_to_ignore.match(filename):
        logging.info('Removing: {0:s}'.format(filename))
        os.remove(filename)

    # Remove previous versions of source directories in the format:
    # project-{version}
    filenames = glob.glob('{0:s}-*'.format(self.project_name))
    for filename in filenames:
      if os.path.isdir(filename) and not filenames_to_ignore.match(filename):
        logging.info('Removing: {0:s}'.format(filename))
        shutil.rmtree(filename)

  def Create(self):
    """Creates the source directory from the source package.

    Returns:
      str: name of the source directory or None on error.
    """
    if not self._source_filename:
      _ = self.Download()

    if not self._source_filename or not os.path.exists(self._source_filename):
      return None

    directory_name = None
    if (self._source_filename.endswith('.tar.bz2') or
        self._source_filename.endswith('.tar.gz') or
        self._source_filename.endswith('.tgz')):
      directory_name = self._CreateFromTar(self._source_filename)

    elif self._source_filename.endswith('.zip'):
      directory_name = self._CreateFromZip(self._source_filename)

    return directory_name

  def Download(self):
    """Downloads the source package.

    Returns:
      str: filename of the source package if the download was successful or
          if the file was already downloaded or None on error.
    """
    if not self._source_filename:
      project_version = self.GetProjectVersion()
      if not project_version:
        return None

      self._source_filename = self._download_helper.Download(
          self.project_name, project_version)

    return self._source_filename

  def GetProjectIdentifier(self):
    """Retrieves the project identifier for a given project name.

    Returns:
      str: project identifier or None on error.
    """
    return self._download_helper.GetProjectIdentifier()

  def GetProjectVersion(self):
    """Retrieves the version number for a given project name.

    Returns:
      str: version number or None on error.
    """
    if not self._project_version:
      version_definition = getattr(self._project_definition, 'version', None)
      self._project_version = self._download_helper.GetLatestVersion(
          self.project_name, version_definition)

    return self._project_version
