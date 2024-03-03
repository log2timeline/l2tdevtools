# -*- coding: utf-8 -*-
"""Helper for building projects from source."""

from l2tdevtools.build_helpers import dpkg
from l2tdevtools.build_helpers import rpm
from l2tdevtools.build_helpers import source
from l2tdevtools.build_helpers import wheel


class BuildHelperFactory(object):
  """Factory class for build helpers."""

  _CONFIGURE_MAKE_BUILD_HELPER_CLASSES = {
      'dpkg': dpkg.ConfigureMakeDPKGBuildHelper,
      'dpkg-source': dpkg.ConfigureMakeSourceDPKGBuildHelper,
      'rpm': rpm.ConfigureMakeRPMBuildHelper,
      'source': source.ConfigureMakeSourceBuildHelper,
      'srpm': rpm.ConfigureMakeSRPMBuildHelper,
      'wheel': wheel.ConfigureMakeWheelBuildHelper,
  }

  _FLIT_BUILD_HELPER_CLASSES = {
      'wheel': wheel.FlitWheelBuildHelper,
  }

  # Note that the rpm and srpm setup.py build helpers are used to build
  # projects that use poetry.
  _POETRY_BUILD_HELPER_CLASSES = {
      'dpkg': dpkg.PybuildDPKGBuildHelper,
      'dpkg-source': dpkg.PybuildSourceDPKGBuildHelper,
      'rpm': rpm.SetupPyRPMBuildHelper,
      'srpm': rpm.SetupPySRPMBuildHelper,
      'wheel': wheel.PoetryWheelBuildHelper,
  }

  _PYPROJECT_BUILD_HELPER_CLASSES = {
      'dpkg': dpkg.PybuildDPKGBuildHelper,
      'dpkg-source': dpkg.PybuildSourceDPKGBuildHelper,
  }

  _SETUP_PY_BUILD_HELPER_CLASSES = {
      'dpkg': dpkg.PybuildDPKGBuildHelper,
      'dpkg-source': dpkg.PybuildSourceDPKGBuildHelper,
      'rpm': rpm.SetupPyRPMBuildHelper,
      'source': source.SetupPySourceBuildHelper,
      'srpm': rpm.SetupPySRPMBuildHelper,
      'wheel': wheel.SetupPyWheelBuildHelper,
  }

  @classmethod
  def NewBuildHelper(
      cls, project_definition, build_target, l2tdevtools_path,
      dependency_definitions):
    """Creates a new build helper.

    Args:
      project_definition (ProjectDefinition): definition of the project
          to build.
      build_target (str): build target.
      l2tdevtools_path (str): path to the l2tdevtools directory.
      dependency_definitions (dict[str, ProjectDefinition]): definitions of all
          projects, which is used to determine the properties of dependencies.

    Returns:
      BuildHelper: build helper or None if build system is not supported.
    """
    if project_definition.build_system == 'configure_make':
      build_helper_class = cls._CONFIGURE_MAKE_BUILD_HELPER_CLASSES.get(
          build_target, None)

    elif project_definition.build_system == 'flit':
      build_helper_class = cls._FLIT_BUILD_HELPER_CLASSES.get(
          build_target, None)

    elif project_definition.build_system == 'poetry':
      build_helper_class = cls._POETRY_BUILD_HELPER_CLASSES.get(
          build_target, None)

    elif project_definition.build_system == 'pyproject':
      build_helper_class = cls._PYPROJECT_BUILD_HELPER_CLASSES.get(
          build_target, None)

    elif project_definition.build_system == 'setup_py':
      build_helper_class = cls._SETUP_PY_BUILD_HELPER_CLASSES.get(
          build_target, None)

    else:
      build_helper_class = None

    if not build_helper_class:
      return None

    return build_helper_class(
        project_definition, l2tdevtools_path, dependency_definitions)
