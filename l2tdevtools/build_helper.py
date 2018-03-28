# -*- coding: utf-8 -*-
"""Helper for building projects from source."""

from __future__ import unicode_literals

from l2tdevtools.build_helpers import dpkg
from l2tdevtools.build_helpers import msi
from l2tdevtools.build_helpers import osc
from l2tdevtools.build_helpers import pkg
from l2tdevtools.build_helpers import rpm
from l2tdevtools.build_helpers import source


class BuildHelperFactory(object):
  """Factory class for build helpers."""

  _CONFIGURE_MAKE_BUILD_HELPER_CLASSES = {
      'dpkg': dpkg.ConfigureMakeDPKGBuildHelper,
      'dpkg-source': dpkg.ConfigureMakeSourceDPKGBuildHelper,
      'msi': msi.ConfigureMakeMSIBuildHelper,
      'osc': osc.ConfigureMakeOSCBuildHelper,
      'pkg': pkg.ConfigureMakePKGBuildHelper,
      'rpm': rpm.ConfigureMakeRPMBuildHelper,
      'source': source.ConfigureMakeSourceBuildHelper,
      'srpm': rpm.ConfigureMakeSRPMBuildHelper,
  }

  _SETUP_PY_BUILD_HELPER_CLASSES = {
      'dpkg': dpkg.SetupPyDPKGBuildHelper,
      'dpkg-source': dpkg.SetupPySourceDPKGBuildHelper,
      'msi': msi.SetupPyMSIBuildHelper,
      'osc': osc.SetupPyOSCBuildHelper,
      'pkg': pkg.SetupPyPKGBuildHelper,
      'rpm': rpm.SetupPyRPMBuildHelper,
      'source': source.SetupPySourceBuildHelper,
      'srpm': rpm.SetupPySRPMBuildHelper,
  }

  @classmethod
  def NewBuildHelper(cls, project_definition, build_target, l2tdevtools_path):
    """Creates a new build helper object.

    Args:
      project_definition (ProjectDefinition): project definition.
      build_target (str): build target.
      l2tdevtools_path (str): path to the l2tdevtools directory.

    Returns:
      BuildHelper: build helper or None if build system is not supported.
    """
    if project_definition.build_system == 'configure_make':
      build_helper_class = cls._CONFIGURE_MAKE_BUILD_HELPER_CLASSES.get(
          build_target, None)

    elif project_definition.build_system == 'setup_py':
      build_helper_class = cls._SETUP_PY_BUILD_HELPER_CLASSES.get(
          build_target, None)

    else:
      build_helper_class = None

    if not build_helper_class:
      return None

    return build_helper_class(project_definition, l2tdevtools_path)
