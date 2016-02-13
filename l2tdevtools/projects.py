# -*- coding: utf-8 -*-
"""Dependency object implementations."""

import logging
import re

try:
  import ConfigParser as configparser
except ImportError:
  import configparser


class ProjectDefinition(object):
  """Class that implements a project definition.

  Attributes:
    architecture_dependent: boolean value to indicate the project is
                            architecture dependent.
    build_dependencies: list of build dependencies.
    build_system: string containing the build system.
    configure_options: list of the configure options.
    description_long: string of the long description of the dependency.
    description_short: string of the short description of the dependency.
    disabled: list containing the names of the build targets that are disabled
              for this dependency.
    dpkg_build_dependencies: list of dpkg build dependencies.
    dpkg_configure_options: list of the configure options when building a deb.
    dpkg_dependencies: list of dpkg dependencies.
    dpkg_name: string of the dpkg package name.
    dpkg_source_name: string of the dpkg source package name.
    dpkg_template_control: string of the name of the dpkg control template file.
    dpkg_template_rules: string of the name of the dpkg rules template file.
    download_url: string of the source package download URL.
    git_url: string of the git repository URL.
    homepage_url: string of the project homepage URL.
    maintainer: string of the name and email address of the maintainer.
    name: string of the name of the dependency.
    setup_name: string of the name used in setup.py.
    osc_build_dependencies: list of osc build dependencies.
    patches: list of patch file names.
    pkg_configure_options: list of the configure options when building a pkg.
    version: the version requirements (instance of DependencyVersion).
  """

  def __init__(self, name):
    """Initializes the project definition.

    Args:
      name: the name of the dependency.
    """
    super(ProjectDefinition, self).__init__()
    self.architecture_dependent = False
    self.build_dependencies = None
    self.build_system = None
    self.configure_options = None
    self.description_long = None
    self.description_short = None
    self.disabled = None
    self.dpkg_build_dependencies = None
    self.dpkg_configure_options = None
    self.dpkg_dependencies = None
    self.dpkg_name = None
    self.dpkg_source_name = None
    self.dpkg_template_control = None
    self.dpkg_template_rules = None
    self.download_url = None
    self.git_url = None
    self.homepage_url = None
    self.maintainer = None
    self.name = name
    self.osc_build_dependencies = None
    self.patches = None
    self.pkg_configure_options = None
    self.setup_name = None
    self.version = None


class DependencyVersion(object):
  """Class that implements a project version."""

  _VERSION_STRING_PART_RE = re.compile(
      r'^(<[=]?|>[=]?|==)([0-9]+)[.]?([0-9]+|)[.]?([0-9]+|)[.-]?([0-9]+|)$')

  def __init__(self, version_string):
    """Initializes the project version.

    Args:
      version_string: the version string.
    """
    super(DependencyVersion, self).__init__()
    self._version_string_parts = []

    if not version_string:
      return

    version_string_parts = version_string.split(u',')
    number_of_version_string_parts = len(version_string_parts)
    if number_of_version_string_parts > 2:
      logging.warning(u'Unsupported version string: {0:s}'.format(
          version_string))
      return

    self._version_string_parts = []
    for index, version_string_part in enumerate(version_string_parts):
      if index == 1 and not version_string_part.startswith(u'<'):
        logging.warning(u'Unsupported version string part: {0:s}'.format(
            version_string_part))
        return

      matches = self._VERSION_STRING_PART_RE.findall(version_string_part)
      if not matches:
        logging.warning(u'Unsupported version string part: {0:s}'.format(
            version_string_part))
        return

      self._version_string_parts.append([
          match for match in matches[0] if match or match == 0])

    self._version_string = version_string

  @property
  def version_string(self):
    """Determines the string representation of the object."""
    return self._version_string


class ProjectDefinitionReader(object):
  """Class that implements a project definition reader."""

  def _GetConfigValue(self, config_parser, section_name, value_name):
    """Retrieves a value from the config parser.

    Args:
      config_parser: the configuration parser (instance of ConfigParser).
      section_name: the name of the section that contains the value.
      value_name: the name of the value.

    Returns:
      An object containing the value or None if the value does not exists.
    """
    try:
      return config_parser.get(section_name, value_name).decode('utf-8')
    except configparser.NoOptionError:
      return

  def Read(self, file_object):
    """Reads project definitions.

    Args:
      file_object: the file-like object to read from.

    Yields:
      Dependency definitions (instances of ProjectDefinition).
    """
    # TODO: replace by:
    # config_parser = configparser. ConfigParser(interpolation=None)
    config_parser = configparser.RawConfigParser()
    config_parser.readfp(file_object)

    for section_name in config_parser.sections():
      project_definition = ProjectDefinition(section_name)

      project_definition.architecture_dependent = self._GetConfigValue(
          config_parser, section_name, u'architecture_dependent')
      project_definition.build_dependencies = self._GetConfigValue(
          config_parser, section_name, u'build_dependencies')
      project_definition.build_system = self._GetConfigValue(
          config_parser, section_name, u'build_system')
      project_definition.configure_options = self._GetConfigValue(
          config_parser, section_name, u'configure_options')
      project_definition.description_long = self._GetConfigValue(
          config_parser, section_name, u'description_long')
      project_definition.description_short = self._GetConfigValue(
          config_parser, section_name, u'description_short')
      project_definition.disabled = self._GetConfigValue(
          config_parser, section_name, u'disabled')
      project_definition.dpkg_build_dependencies = self._GetConfigValue(
          config_parser, section_name, u'dpkg_build_dependencies')
      project_definition.dpkg_configure_options = self._GetConfigValue(
          config_parser, section_name, u'dpkg_configure_options')
      project_definition.dpkg_dependencies = self._GetConfigValue(
          config_parser, section_name, u'dpkg_dependencies')
      project_definition.dpkg_name = self._GetConfigValue(
          config_parser, section_name, u'dpkg_name')
      project_definition.dpkg_source_name = self._GetConfigValue(
          config_parser, section_name, u'dpkg_source_name')
      project_definition.dpkg_template_control = self._GetConfigValue(
          config_parser, section_name, u'dpkg_template_control')
      project_definition.dpkg_template_rules = self._GetConfigValue(
          config_parser, section_name, u'dpkg_template_rules')
      project_definition.download_url = self._GetConfigValue(
          config_parser, section_name, u'download_url')
      project_definition.git_url = self._GetConfigValue(
          config_parser, section_name, u'git_url')
      project_definition.homepage_url = self._GetConfigValue(
          config_parser, section_name, u'homepage_url')
      project_definition.maintainer = self._GetConfigValue(
          config_parser, section_name, u'maintainer')
      project_definition.osc_build_dependencies = self._GetConfigValue(
          config_parser, section_name, u'osc_build_dependencies')
      project_definition.patches = self._GetConfigValue(
          config_parser, section_name, u'patches')
      project_definition.pkg_configure_options = self._GetConfigValue(
          config_parser, section_name, u'pkg_configure_options')
      project_definition.setup_name = self._GetConfigValue(
          config_parser, section_name, u'setup_name')
      project_definition.version = self._GetConfigValue(
          config_parser, section_name, u'version')

      if project_definition.build_dependencies is None:
        project_definition.build_dependencies = []
      elif isinstance(
          project_definition.build_dependencies, basestring):
        project_definition.build_dependencies = (
            project_definition.build_dependencies.split(u','))

      if project_definition.configure_options is None:
        project_definition.configure_options = []
      elif isinstance(
          project_definition.configure_options, basestring):
        project_definition.configure_options = (
            project_definition.configure_options.split(u','))

      if project_definition.disabled is None:
        project_definition.disabled = []
      elif isinstance(project_definition.disabled, basestring):
        project_definition.disabled = project_definition.disabled.split(
            u',')

      if project_definition.dpkg_build_dependencies is None:
        project_definition.dpkg_build_dependencies = []
      elif isinstance(
          project_definition.dpkg_build_dependencies, basestring):
        project_definition.dpkg_build_dependencies = (
            project_definition.dpkg_build_dependencies.split(u','))

      if project_definition.dpkg_configure_options is None:
        project_definition.dpkg_configure_options = []
      elif isinstance(
          project_definition.dpkg_configure_options, basestring):
        project_definition.dpkg_configure_options = (
            project_definition.dpkg_configure_options.split(u','))

      if project_definition.dpkg_dependencies is None:
        project_definition.dpkg_dependencies = []
      elif isinstance(project_definition.dpkg_dependencies, basestring):
        project_definition.dpkg_dependencies = (
            project_definition.dpkg_dependencies.split(u','))

      if project_definition.osc_build_dependencies is None:
        project_definition.osc_build_dependencies = []
      elif isinstance(
          project_definition.osc_build_dependencies, basestring):
        project_definition.osc_build_dependencies = (
            project_definition.osc_build_dependencies.split(u','))

      if project_definition.patches is None:
        project_definition.patches = []
      elif isinstance(project_definition.patches, basestring):
        project_definition.patches = project_definition.patches.split(
            u',')

      if project_definition.pkg_configure_options is None:
        project_definition.pkg_configure_options = []
      elif isinstance(
          project_definition.pkg_configure_options, basestring):
        project_definition.pkg_configure_options = (
            project_definition.pkg_configure_options.split(u','))

      # Need at minimum a name and a download URL.
      if project_definition.name and project_definition.download_url:
        yield project_definition

      project_definition.version = DependencyVersion(
          project_definition.version)
