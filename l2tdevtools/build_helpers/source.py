# -*- coding: utf-8 -*-
"""Helper for building projects from source."""

from __future__ import unicode_literals

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
    source_filename = source_helper_object.Download()
    if not source_filename:
      logging.info('Download of: {0:s} failed'.format(
          source_helper_object.project_name))
      return False

    source_directory = source_helper_object.Create()
    if not source_directory:
      logging.error(
          'Extraction of source package: {0:s} failed'.format(source_filename))
      return False

    logging.info('Building source of: {0:s}'.format(source_filename))

    if self._project_definition.patches:
      # TODO: add self._ApplyPatches
      pass

    log_file_path = os.path.join('..', self.LOG_FILENAME)
    command = './configure > {0:s} 2>&1'.format(log_file_path)
    exit_code = subprocess.call('(cd {0:s} && {1:s})'.format(
        source_directory, command), shell=True)
    if exit_code != 0:
      logging.error('Running: "{0:s}" failed.'.format(command))
      return False

    command = 'make >> {0:s} 2>&1'.format(log_file_path)
    exit_code = subprocess.call('(cd {0:s} && {1:s})'.format(
        source_directory, command), shell=True)
    if exit_code != 0:
      logging.error('Running: "{0:s}" failed.'.format(command))
      return False

    return True

  def Clean(self, unused_source_helper_object):
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
    source_filename = source_helper_object.Download()
    if not source_filename:
      logging.info('Download of: {0:s} failed'.format(
          source_helper_object.project_name))
      return False

    source_directory = source_helper_object.Create()
    if not source_directory:
      logging.error(
          'Extraction of source package: {0:s} failed'.format(source_filename))
      return False

    logging.info('Building source of: {0:s}'.format(source_filename))

    if self._project_definition.patches:
      # TODO: add self._ApplyPatches
      pass

    log_file_path = os.path.join('..', self.LOG_FILENAME)
    command = '{0:s} setup.py build > {1:s} 2>&1'.format(
        sys.executable, log_file_path)
    exit_code = subprocess.call('(cd {0:s} && {1:s})'.format(
        source_directory, command), shell=True)
    if exit_code != 0:
      logging.error('Running: "{0:s}" failed.'.format(command))
      return False

    return True
