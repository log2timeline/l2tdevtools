# -*- coding: utf-8 -*-
"""Helper for building projects from source."""

import logging
import os
import subprocess
import sys

from l2tdevtools.build_helpers import interface


class SourceBuildHelper(interface.BuildHelper):
  """Helper to build projects from source."""


class ConfigureMakeSourceBuildHelper(SourceBuildHelper):
  """Helper to build projects from source using configure and make."""

  def Build(self, source_helper_object):
    """Builds the source.

    Args:
      source_helper_object (SourceHelper): source helper.

    Returns:
      bool: True if successful, False otherwise.
    """
    project_name = source_helper_object.project_name

    source_package_path = source_helper_object.GetSourcePackagePath()
    if not source_package_path:
      logging.info(f'Missing source package of: {project_name:s}')
      return False

    source_directory = source_helper_object.GetSourceDirectoryPath()
    if not source_directory:
      logging.info(f'Missing source directory of: {project_name:s}')
      return False

    source_package_filename = source_helper_object.GetSourcePackageFilename()
    logging.info(f'Building source of: {source_package_filename:s}')

    log_file_path = os.path.join('..', self.LOG_FILENAME)
    command = f'./configure > {log_file_path:s} 2>&1'
    exit_code = subprocess.call(
        f'(cd {source_directory:s} && {command:s})', shell=True)
    if exit_code != 0:
      logging.error(f'Running: "{command:s}" failed.')
      return False

    command = f'make >> {log_file_path:s} 2>&1'
    exit_code = subprocess.call(
        f'(cd {source_directory:s} && {command:s})', shell=True)
    if exit_code != 0:
      logging.error(f'Running: "{command:s}" failed.')
      return False

    return True

  # pylint: disable=unused-argument
  def Clean(self, source_helper_object):
    """Cleans the source.

    Args:
      source_helper_object (SourceHelper): source helper.
    """
    # TODO: implement.
    return


class SetupPySourceBuildHelper(SourceBuildHelper):
  """Helper to build projects from source using setup.py."""

  def Build(self, source_helper_object):
    """Builds the source.

    Args:
      source_helper_object (SourceHelper): source helper.

    Returns:
      bool: True if successful, False otherwise.
    """
    project_name = source_helper_object.project_name

    source_package_path = source_helper_object.GetSourcePackagePath()
    if not source_package_path:
      logging.info(f'Missing source package of: {project_name:s}')
      return False

    source_directory = source_helper_object.GetSourceDirectoryPath()
    if not source_directory:
      logging.info(f'Missing source directory of: {project_name:s}')
      return False

    source_package_filename = source_helper_object.GetSourcePackageFilename()
    logging.info(f'Building source of: {source_package_filename:s}')

    log_file_path = os.path.join('..', self.LOG_FILENAME)
    command = f'{sys.executable:s} setup.py build > {log_file_path:s} 2>&1'
    exit_code = subprocess.call(
        f'(cd {source_directory:s} && {command:s})', shell=True)
    if exit_code != 0:
      logging.error(f'Running: "{command:s}" failed.')
      return False

    return True
