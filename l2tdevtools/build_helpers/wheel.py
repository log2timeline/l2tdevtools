# -*- coding: utf-8 -*-
"""Helper for building Python wheel packages (.whl)."""

import glob
import logging
import os
import platform
import re
import shutil
import subprocess
import sys

from l2tdevtools.build_helpers import interface


class WheelBuildHelper(interface.BuildHelper):
  """Helper to build Python wheel packages (.whl)."""

  _NON_PYTHON_DEPENDENCIES = frozenset(['fuse', 'libcrypto', 'zlib'])

  def __init__(
      self, project_definition, l2tdevtools_path, dependency_definitions):
    """Initializes a build helper.

    Args:
      project_definition (ProjectDefinition): definition of the project
          to build.
      l2tdevtools_path (str): path to the l2tdevtools directory.
      dependency_definitions (dict[str, ProjectDefinition]): definitions of all
          projects, which is used to determine the properties of dependencies.
    """
    super(WheelBuildHelper, self).__init__(
        project_definition, l2tdevtools_path, dependency_definitions)
    self.architecture = None

    # Note that platform.machine() does not indicate if a 32-bit version of
    # Python is running on a 64-bit machine, hence we need to use
    # platform.architecture() instead.
    architecture = platform.architecture()[0]
    if architecture == '32bit':
      self.architecture = 'win32'
    elif architecture == '64bit':
      self.architecture = 'win_amd64'

  def _GetWheelFilenameProjectInformation(self, source_helper_object):
    """Determines the project name and version used by the wheel filename.

    Args:
      source_helper_object (SourceHelper): source helper.

    Returns:
      tuple: containing:

        * str: project name used by the wheel filename.
        * str: project version used by the wheel filename.
    """
    if self._project_definition.wheel_name:
      project_name = self._project_definition.wheel_name
    elif self._project_definition.setup_name:
      project_name = self._project_definition.setup_name
    else:
      project_name = source_helper_object.project_name

    project_version = source_helper_object.GetProjectVersion()

    return project_name, project_version

  def _MoveWheel(self, source_helper_object):
    """Moves the wheel from the dist sub directory into the build directory.

    Args:
      source_helper_object (SourceHelper): source helper.

    Returns:
      bool: True if the move was successful, False otherwise.
    """
    project_name, _ = self._GetWheelFilenameProjectInformation(
        source_helper_object)

    source_directory = source_helper_object.GetSourceDirectoryPath()
    if not source_directory:
      logging.info('Missing source directory of: {0:s}'.format(
          source_helper_object.project_name))
      return False

    filenames_glob = os.path.join(
        source_directory, 'dist', '{0:s}-*-*-*.whl'.format(project_name))
    filenames = glob.glob(filenames_glob)

    if len(filenames) != 1:
      logging.error('Unable to find wheel file: {0:s}.'.format(filenames_glob))
      return False

    _, _, wheel_filename = filenames[0].rpartition(os.path.sep)
    if os.path.exists(wheel_filename):
      logging.warning('Wheel file already exists.')
    else:
      logging.info('Moving: {0:s}'.format(filenames[0]))
      shutil.move(filenames[0], '.')

    return True

  def CheckBuildDependencies(self):
    """Checks if the build dependencies are met.

    Returns:
      list[str]: build dependency names that are not met or an empty list.
    """
    missing_packages = []
    for package_name in self._project_definition.build_dependencies:
      if package_name not in self._NON_PYTHON_DEPENDENCIES:
        missing_packages.append(package_name)

    return missing_packages

  def CheckBuildRequired(self, source_helper_object):
    """Checks if a build is required.

    Args:
      source_helper_object (SourceHelper): source helper.

    Returns:
      bool: True if a build is required, False otherwise.
    """
    project_name, project_version = self._GetWheelFilenameProjectInformation(
        source_helper_object)

    filenames_glob = '{0:s}-{1:s}-*-*-*.whl'.format(
        project_name, project_version)

    return not glob.glob(filenames_glob)

  def Clean(self, source_helper_object):
    """Cleans the build and dist directory.

    Args:
      source_helper_object (SourceHelper): source helper.
    """
    # Remove previous versions of wheels.
    project_name, project_version = self._GetWheelFilenameProjectInformation(
        source_helper_object)

    filenames_to_ignore = '{0:s}-{1:s}-.*-.*-.*.whl'.format(
        project_name, project_version)
    filenames_to_ignore = re.compile(filenames_to_ignore)

    filenames_glob = '{0:s}-*-*-*.whl'.format(project_name)
    filenames = glob.glob(filenames_glob)

    for filename in filenames:
      if not filenames_to_ignore.match(filename):
        logging.info('Removing: {0:s}'.format(filename))
        os.remove(filename)


class ConfigureMakeWheelBuildHelper(WheelBuildHelper):
  """Helper to build Python wheel packages (.whl).

  Builds wheel packages for projects that use configure/make as their build
  system.
  """

  def Build(self, source_helper_object):
    """Builds the wheel.

    Args:
      source_helper_object (SourceHelper): source helper.

    Returns:
      bool: True if successful, False otherwise.

    Raises:
      RuntimeError: if setup.py is missing and a wheel cannot be build.
    """
    source_package_path = source_helper_object.GetSourcePackagePath()
    if not source_package_path:
      logging.info('Missing source package of: {0:s}'.format(
          source_helper_object.project_name))
      return False

    source_directory = source_helper_object.GetSourceDirectoryPath()
    if not source_directory:
      logging.info('Missing source directory of: {0:s}'.format(
          source_helper_object.project_name))
      return False

    source_package_filename = source_helper_object.GetSourcePackageFilename()
    logging.info('Building wheel of: {0:s}'.format(source_package_filename))

    setup_py_path = os.path.join(source_directory, 'setup.py')
    if not os.path.exists(setup_py_path):
      raise RuntimeError('Missing setup.py cannot build wheel')

    log_file_path = os.path.join('..', self.LOG_FILENAME)
    command = '\"{0:s}\" setup.py bdist_wheel > {1:s} 2>&1'.format(
        sys.executable, log_file_path)
    exit_code = subprocess.call('(cd {0:s} && {1:s})'.format(
        source_directory, command), shell=True)
    if exit_code != 0:
      logging.error('Running: "{0:s}" failed.'.format(command))
      return False

    return self._MoveWheel(source_helper_object)


class SetupPyWheelBuildHelper(WheelBuildHelper):
  """Helper to build Python wheel packages (.whl).

  Builds wheel packages for projects that use setup.py as their build system.
  """

  def Build(self, source_helper_object):
    """Builds the wheel.

    Args:
      source_helper_object (SourceHelper): source helper.

    Returns:
      bool: True if successful, False otherwise.
    """
    source_package_path = source_helper_object.GetSourcePackagePath()
    if not source_package_path:
      logging.info('Missing source package of: {0:s}'.format(
          source_helper_object.project_name))
      return False

    source_directory = source_helper_object.GetSourceDirectoryPath()
    if not source_directory:
      logging.info('Missing source directory of: {0:s}'.format(
          source_helper_object.project_name))
      return False

    source_package_filename = source_helper_object.GetSourcePackageFilename()
    logging.info('Building wheel of: {0:s}'.format(source_package_filename))

    log_file_path = os.path.join('..', self.LOG_FILENAME)
    command = '\"{0:s}\" setup.py bdist_wheel > {1:s} 2>&1'.format(
        sys.executable, log_file_path)
    exit_code = subprocess.call('(cd {0:s} && {1:s})'.format(
        source_directory, command), shell=True)
    if exit_code != 0:
      logging.error('Running: "{0:s}" failed.'.format(command))
      return False

    return self._MoveWheel(source_helper_object)


class FlitWheelBuildHelper(WheelBuildHelper):
  """Helper to build Python wheel packages (.whl) using flit."""

  def Build(self, source_helper_object):
    """Builds the wheel.

    Args:
      source_helper_object (SourceHelper): source helper.

    Returns:
      bool: True if successful, False otherwise.
    """
    source_package_path = source_helper_object.GetSourcePackagePath()
    if not source_package_path:
      logging.info('Missing source package of: {0:s}'.format(
          source_helper_object.project_name))
      return False

    source_directory = source_helper_object.GetSourceDirectoryPath()
    if not source_directory:
      logging.info('Missing source directory of: {0:s}'.format(
          source_helper_object.project_name))
      return False

    source_package_filename = source_helper_object.GetSourcePackageFilename()
    logging.info('Building wheel of: {0:s}'.format(source_package_filename))

    log_file_path = os.path.join('..', self.LOG_FILENAME)
    command = '\"{0:s}\" -m flit build --format wheel > {1:s} 2>&1'.format(
        sys.executable, log_file_path)
    exit_code = subprocess.call('(cd {0:s} && {1:s})'.format(
        source_directory, command), shell=True)
    if exit_code != 0:
      logging.error('Running: "{0:s}" failed.'.format(command))
      return False

    return self._MoveWheel(source_helper_object)


class PoetryWheelBuildHelper(WheelBuildHelper):
  """Helper to build Python wheel packages (.whl) using poetry."""

  def Build(self, source_helper_object):
    """Builds the wheel.

    Args:
      source_helper_object (SourceHelper): source helper.

    Returns:
      bool: True if successful, False otherwise.
    """
    source_package_path = source_helper_object.GetSourcePackagePath()
    if not source_package_path:
      logging.info('Missing source package of: {0:s}'.format(
          source_helper_object.project_name))
      return False

    source_directory = source_helper_object.GetSourceDirectoryPath()
    if not source_directory:
      logging.info('Missing source directory of: {0:s}'.format(
          source_helper_object.project_name))
      return False

    source_package_filename = source_helper_object.GetSourcePackageFilename()
    logging.info('Building wheel of: {0:s}'.format(source_package_filename))

    log_file_path = os.path.join('..', self.LOG_FILENAME)
    command = '\"{0:s}\" -m poetry build --format wheel > {1:s} 2>&1'.format(
        sys.executable, log_file_path)
    exit_code = subprocess.call('(cd {0:s} && {1:s})'.format(
        source_directory, command), shell=True)
    if exit_code != 0:
      logging.error('Running: "{0:s}" failed.'.format(command))
      return False

    return self._MoveWheel(source_helper_object)
