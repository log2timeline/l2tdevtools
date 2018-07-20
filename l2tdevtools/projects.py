# -*- coding: utf-8 -*-
"""Project definitions."""

from __future__ import unicode_literals

import logging
import re
import sys

try:
  import ConfigParser as configparser
except ImportError:
  import configparser  # pylint: disable=import-error

from l2tdevtools import py2to3


class ProjectDefinition(object):
  """Project definition.

  Attributes:
    architecture_dependent (bool): True if the project is architecture
        dependent.
    build_dependencies (list[str]): build dependencies.
    build_options (list[str]): build options. Current supported build options
        are: python2_only (to only build for Python version 2).
    build_system (str): build system.
    configure_options (list[str]): configure options.
    description_long (str): long description of the project.
    description_short (str): short description of the project.
    disabled (list[str]): names of the build targets that are disabled for
        this project.
    dpkg_build_dependencies (list[str]): dpkg build dependencies.
    dpkg_configure_options (list[str]): configure options when building a deb.
    dpkg_dependencies (list[str]): dpkg dependencies.
    dpkg_name (str): dpkg package name.
    dpkg_source_format (str): dpkg source format, either "native" or "quilt".
    dpkg_source_name (str): dpkg source package name.
    dpkg_template_control (str): name of the dpkg control template file.
    dpkg_template_install_python2 (list[str]): names of the dpkg Python 2
        install template files.
    dpkg_template_install_python3 (list[str]): names of the dpkg Python 3
        install template files.
    dpkg_template_rules (str): name of the dpkg rules template file.
    download_url (str): source package download URL.
    git_url (str): git repository URL.
    homepage_url (str): project homepage URL.
    maintainer (str): name and email address of the maintainer.
    msi_name (str): MSI package name.
    name (str): name of the project.
    setup_name (str): project name used in setup.py.
    rpm_build_dependencies (list[str]): rpm build dependencies.
    rpm_name (str): RPM package name.
    rpm_python2_prefix (str): Python 2 RPM package prefix.
    rpm_template_spec (str): name of the rpm spec file.
    patches (list[str]): patch file names.
    pkg_configure_options (list[str]): configure options when building a pkg.
    version (ProjectVersionDefinition): version requirements.
  """

  def __init__(self, name):
    """Initializes a project definition.

    Args:
      name (str): name of the project.
    """
    super(ProjectDefinition, self).__init__()
    self.architecture_dependent = False
    self.build_dependencies = None
    self.build_options = None
    self.build_system = None
    self.configure_options = None
    self.description_long = None
    self.description_short = None
    self.disabled = None
    self.dpkg_build_dependencies = None
    self.dpkg_configure_options = None
    self.dpkg_dependencies = None
    self.dpkg_name = None
    self.dpkg_source_format = None
    self.dpkg_source_name = None
    self.dpkg_template_control = None
    self.dpkg_template_install_python2 = None
    self.dpkg_template_install_python3 = None
    self.dpkg_template_rules = None
    self.download_url = None
    self.git_url = None
    self.homepage_url = None
    self.maintainer = None
    self.msi_name = None
    self.name = name
    self.msi_prebuild = None
    self.rpm_build_dependencies = None
    self.rpm_name = None
    self.rpm_python2_prefix = None
    self.rpm_template_spec = None
    self.patches = None
    self.pkg_configure_options = None
    self.setup_name = None
    self.version = None

  def IsPython2Only(self):
    """Determines if the project only supports Python version 2.

    Note that Python 3 is supported as of 3.4 any earlier version is not
    seen as compatible.

    Returns:
      bool: True if the project only support Python version 2.
    """
    return self.build_options and 'python2_only' in self.build_options


class ProjectVersionDefinition(object):
  """Project version definition."""

  _VERSION_STRING_PART_RE = re.compile(
      r'^(<[=]?|>[=]?|==)([0-9]+)[.]?([0-9]+|)[.]?([0-9]+|)[.-]?([0-9]+|)$')

  def __init__(self, version_string):
    """Initializes a project version definition.

    Args:
      version_string (str): version string.
    """
    super(ProjectVersionDefinition, self).__init__()
    self._version_string_parts = []

    if not version_string:
      return

    version_string_parts = version_string.split(',')
    number_of_version_string_parts = len(version_string_parts)
    if number_of_version_string_parts > 2:
      logging.warning('Unsupported version string: {0:s}'.format(
          version_string))
      return

    self._version_string_parts = []
    for index, version_string_part in enumerate(version_string_parts):
      if index == 1 and not version_string_part.startswith('<'):
        logging.warning('Unsupported version string part: {0:s}'.format(
            version_string_part))
        return

      matches = self._VERSION_STRING_PART_RE.findall(version_string_part)
      if not matches:
        logging.warning('Unsupported version string part: {0:s}'.format(
            version_string_part))
        return

      self._version_string_parts.append([
          match for match in matches[0] if match or match == 0])

    self._version_string = version_string

  @property
  def version_string(self):
    """str: string representation of the object."""
    return self._version_string

  def GetEarliestVersion(self):
    """Retrieves the earliest version.

    Returns:
      str: earliest version or None if version string parts are missing.
    """
    if not self._version_string_parts:
      return None

    return self._version_string_parts[0]

  def GetLatestVersion(self):
    """Retrieves the latest version.

    Returns:
      str: latest version or None if version string parts are missing.
    """
    if not self._version_string_parts or len(self._version_string_parts) == 1:
      return None

    return self._version_string_parts[1]


class ProjectDefinitionReader(object):
  """Project definition reader."""

  def _GetConfigValue(self, config_parser, section_name, value_name):
    """Retrieves a value from the config parser.

    Args:
      config_parser (ConfigParser): configuration parser.
      section_name (str): name of the section that contains the value.
      value_name (str): name of the value.

    Returns:
      object: value or None if the value does not exists.
    """
    try:
      return config_parser.get(section_name, value_name)
    except configparser.NoOptionError:
      return None

  def Read(self, file_object):
    """Reads project definitions.

    Args:
      file_object (file): file-like object to read from.

    Yields:
      ProjectDefinition: project definition.
    """
    # TODO: replace by:
    # config_parser = configparser. ConfigParser(interpolation=None)
    config_parser = configparser.RawConfigParser()

    if sys.version_info[0] < 3:
      config_parser.readfp(file_object)  # pylint: disable=deprecated-method
    else:
      config_parser.read_file(file_object)

    for section_name in config_parser.sections():
      project_definition = ProjectDefinition(section_name)

      project_definition.architecture_dependent = self._GetConfigValue(
          config_parser, section_name, 'architecture_dependent')
      project_definition.build_dependencies = self._GetConfigValue(
          config_parser, section_name, 'build_dependencies')
      project_definition.build_options = self._GetConfigValue(
          config_parser, section_name, 'build_options')
      project_definition.build_system = self._GetConfigValue(
          config_parser, section_name, 'build_system')
      project_definition.configure_options = self._GetConfigValue(
          config_parser, section_name, 'configure_options')
      project_definition.description_long = self._GetConfigValue(
          config_parser, section_name, 'description_long')
      project_definition.description_short = self._GetConfigValue(
          config_parser, section_name, 'description_short')
      project_definition.disabled = self._GetConfigValue(
          config_parser, section_name, 'disabled')
      project_definition.dpkg_build_dependencies = self._GetConfigValue(
          config_parser, section_name, 'dpkg_build_dependencies')
      project_definition.dpkg_configure_options = self._GetConfigValue(
          config_parser, section_name, 'dpkg_configure_options')
      project_definition.dpkg_dependencies = self._GetConfigValue(
          config_parser, section_name, 'dpkg_dependencies')
      project_definition.dpkg_name = self._GetConfigValue(
          config_parser, section_name, 'dpkg_name')
      project_definition.dpkg_source_format = self._GetConfigValue(
          config_parser, section_name, 'dpkg_source_format')
      project_definition.dpkg_source_name = self._GetConfigValue(
          config_parser, section_name, 'dpkg_source_name')
      project_definition.dpkg_template_control = self._GetConfigValue(
          config_parser, section_name, 'dpkg_template_control')
      project_definition.dpkg_template_install_python2 = self._GetConfigValue(
          config_parser, section_name, 'dpkg_template_install_python2')
      project_definition.dpkg_template_install_python3 = self._GetConfigValue(
          config_parser, section_name, 'dpkg_template_install_python3')
      project_definition.dpkg_template_rules = self._GetConfigValue(
          config_parser, section_name, 'dpkg_template_rules')
      project_definition.download_url = self._GetConfigValue(
          config_parser, section_name, 'download_url')
      project_definition.git_url = self._GetConfigValue(
          config_parser, section_name, 'git_url')
      project_definition.homepage_url = self._GetConfigValue(
          config_parser, section_name, 'homepage_url')
      project_definition.maintainer = self._GetConfigValue(
          config_parser, section_name, 'maintainer')
      project_definition.msi_name = self._GetConfigValue(
          config_parser, section_name, 'msi_name')
      project_definition.msi_prebuild = self._GetConfigValue(
          config_parser, section_name, 'msi_prebuild')
      project_definition.rpm_build_dependencies = self._GetConfigValue(
          config_parser, section_name, 'rpm_build_dependencies')
      project_definition.rpm_name = self._GetConfigValue(
          config_parser, section_name, 'rpm_name')
      project_definition.rpm_python2_prefix = self._GetConfigValue(
          config_parser, section_name, 'rpm_python2_prefix')
      project_definition.rpm_template_spec = self._GetConfigValue(
          config_parser, section_name, 'rpm_template_spec')
      project_definition.patches = self._GetConfigValue(
          config_parser, section_name, 'patches')
      project_definition.pkg_configure_options = self._GetConfigValue(
          config_parser, section_name, 'pkg_configure_options')
      project_definition.setup_name = self._GetConfigValue(
          config_parser, section_name, 'setup_name')
      project_definition.version = self._GetConfigValue(
          config_parser, section_name, 'version')

      if project_definition.build_dependencies is None:
        project_definition.build_dependencies = []
      elif isinstance(
          project_definition.build_dependencies, py2to3.STRING_TYPES):
        project_definition.build_dependencies = (
            project_definition.build_dependencies.split(','))

      if project_definition.build_options is None:
        project_definition.build_options = []
      elif isinstance(
          project_definition.build_options, py2to3.STRING_TYPES):
        project_definition.build_options = (
            project_definition.build_options.split(','))

      if project_definition.configure_options is None:
        project_definition.configure_options = []
      elif isinstance(
          project_definition.configure_options, py2to3.STRING_TYPES):
        project_definition.configure_options = (
            project_definition.configure_options.split(','))

      if project_definition.disabled is None:
        project_definition.disabled = []
      elif isinstance(project_definition.disabled, py2to3.STRING_TYPES):
        project_definition.disabled = project_definition.disabled.split(
            ',')

      if project_definition.dpkg_build_dependencies is None:
        project_definition.dpkg_build_dependencies = []
      elif isinstance(
          project_definition.dpkg_build_dependencies, py2to3.STRING_TYPES):
        project_definition.dpkg_build_dependencies = (
            project_definition.dpkg_build_dependencies.split(','))

      if project_definition.dpkg_configure_options is None:
        project_definition.dpkg_configure_options = []
      elif isinstance(
          project_definition.dpkg_configure_options, py2to3.STRING_TYPES):
        project_definition.dpkg_configure_options = (
            project_definition.dpkg_configure_options.split(','))

      if project_definition.dpkg_dependencies is None:
        project_definition.dpkg_dependencies = []
      elif isinstance(
          project_definition.dpkg_dependencies, py2to3.STRING_TYPES):
        project_definition.dpkg_dependencies = (
            project_definition.dpkg_dependencies.split(','))

      if project_definition.dpkg_template_install_python2 is None:
        project_definition.dpkg_template_install_python2 = []
      elif isinstance(
          project_definition.dpkg_template_install_python2,
          py2to3.STRING_TYPES):
        project_definition.dpkg_template_install_python2 = (
            project_definition.dpkg_template_install_python2.split(','))

      if project_definition.dpkg_template_install_python3 is None:
        project_definition.dpkg_template_install_python3 = []
      elif isinstance(
          project_definition.dpkg_template_install_python3,
          py2to3.STRING_TYPES):
        project_definition.dpkg_template_install_python3 = (
            project_definition.dpkg_template_install_python3.split(','))

      if project_definition.rpm_build_dependencies is None:
        project_definition.rpm_build_dependencies = []
      elif isinstance(
          project_definition.rpm_build_dependencies, py2to3.STRING_TYPES):
        project_definition.rpm_build_dependencies = (
            project_definition.rpm_build_dependencies.split(','))

      if project_definition.patches is None:
        project_definition.patches = []
      elif isinstance(project_definition.patches, py2to3.STRING_TYPES):
        project_definition.patches = project_definition.patches.split(
            ',')

      if project_definition.pkg_configure_options is None:
        project_definition.pkg_configure_options = []
      elif isinstance(
          project_definition.pkg_configure_options, py2to3.STRING_TYPES):
        project_definition.pkg_configure_options = (
            project_definition.pkg_configure_options.split(','))

      # Need at minimum a name and a download URL.
      if project_definition.name and project_definition.download_url:
        yield project_definition

      project_definition.version = ProjectVersionDefinition(
          project_definition.version)
