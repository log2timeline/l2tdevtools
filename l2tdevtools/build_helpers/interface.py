# -*- coding: utf-8 -*-
"""Helper for building projects from source."""

from __future__ import unicode_literals

import os


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
