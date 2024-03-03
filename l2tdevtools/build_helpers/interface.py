# -*- coding: utf-8 -*-
"""Helper for building projects from source."""

import glob
import logging
import os
import re
import shutil


class BuildHelper(object):
  """Helper to build projects from source."""

  LOG_FILENAME = 'build.log'

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
    super(BuildHelper, self).__init__()
    self._data_path = os.path.join(l2tdevtools_path, 'data')
    self._dependency_definitions = dependency_definitions
    self._project_definition = project_definition

  def _RemoveOlderSourceDirectories(self, project_name, project_version):
    """Removes previous versions of source directories.

    Args:
      project_name (str): name of the project.
      project_version (str): version of the project.
    """
    filenames_to_ignore = re.compile(
        '^{0:s}-.*{1!s}'.format(project_name, project_version))

    # Remove previous versions of source directories in the format:
    # <project>-[0-9]*
    filenames = glob.glob('{0:s}-[0-9]*'.format(project_name))
    for filename in filenames:
      if os.path.isdir(filename) and not filenames_to_ignore.match(filename):
        logging.info('Removing: {0:s}'.format(filename))
        shutil.rmtree(filename, ignore_errors=True)

  def _RemoveOlderSourcePackages(self, project_name, project_version):
    """Removes previous versions of source packages.

    Args:
      project_name (str): name of the project.
      project_version (str): version of the project.
    """
    filenames_to_ignore = re.compile(
        '^{0:s}-.*{1!s}'.format(project_name, project_version))

    # Remove previous versions of source packages in the format:
    # <project>-[0-9]*.tar.gz
    filenames = glob.glob('{0:s}-[0-9]*.tar.gz'.format(project_name))
    for filename in filenames:
      if not filenames_to_ignore.match(filename):
        logging.info('Removing: {0:s}'.format(filename))
        os.remove(filename)

    # Remove previous versions of source packages in the format:
    # <project>-[0-9]*.tgz
    filenames = glob.glob('{0:s}-[0-9]*.tgz'.format(project_name))
    for filename in filenames:
      if not filenames_to_ignore.match(filename):
        logging.info('Removing: {0:s}'.format(filename))
        os.remove(filename)

    # Remove previous versions of source packages in the format:
    # <project>-[0-9]*.zip
    filenames = glob.glob('{0:s}-[0-9]*.zip'.format(project_name))
    for filename in filenames:
      if not filenames_to_ignore.match(filename):
        logging.info('Removing: {0:s}'.format(filename))
        os.remove(filename)

  def CheckBuildDependencies(self):
    """Checks if the build dependencies are met.

    Returns:
      list[str]: build dependency names that are not met or an empty list.
    """
    build_dependencies = self._project_definition.build_dependencies
    if not build_dependencies:
      build_dependencies = []
    return list(build_dependencies)

  # pylint: disable=unused-argument
  def CheckBuildRequired(self, source_helper_object):
    """Checks if a build is required.

    Args:
      source_helper_object (SourceHelper): source helper.

    Returns:
      bool: True if a build is required, False otherwise.
    """
    return True

  def CheckProjectConfiguration(self):
    """Checks if the project configuration is correct.

    Returns:
      bool: True if the project configuration is correct, False otherwise.
    """
    return True
