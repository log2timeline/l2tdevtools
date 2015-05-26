# -*- coding: utf-8 -*-
"""Dependency object implementations."""

import logging
import re

try:
  import ConfigParser as configparser
except ImportError:
  import configparser


class DependencyDefinition(object):
  """Class that implements a dependency definition."""

  def __init__(self, name):
    """Initializes the dependency definition.

    Args:
      name: the name of the dependency.
    """
    super(DependencyDefinition, self).__init__()
    self.architecture_dependent = False
    self.build_system = None
    self.description_long = None
    self.description_short = None
    self.disabled = None
    self.dpkg_build_dependencies = None
    self.dpkg_dependencies = None
    self.dpkg_manual_install = False
    self.dpkg_name = None
    self.download_url = None
    self.homepage_url = None
    self.maintainer = None
    self.name = name
    self.setup_name = None
    self.patches = None
    self.version = None


class DependencyVersion(object):
  """Class that implements a dependency version."""

  _VERSION_STRING_PART_RE = re.compile(
      r'^(<[=]?|>[=]?|==)([0-9]+)[.]?([0-9]+|)[.]?([0-9]+|)[.-]?([0-9]+|)$')

  def __init__(self, version_string):
    """Initializes the dependency version.

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


class DependencyDefinitionReader(object):
  """Class that implements a dependency definition reader."""

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
    """Reads dependency definitions.

    Args:
      file_object: the file-like object to read from.

    Yields:
      Dependency definitions (instances of DependencyDefinition).
    """
    # TODO: replace by:
    # config_parser = configparser. ConfigParser(interpolation=None)
    config_parser = configparser.RawConfigParser()
    config_parser.readfp(file_object)

    for section_name in config_parser.sections():
      dependency_definition = DependencyDefinition(section_name)

      dependency_definition.architecture_dependent = self._GetConfigValue(
          config_parser, section_name, u'architecture_dependent')
      dependency_definition.build_system = self._GetConfigValue(
          config_parser, section_name, u'build_system')
      dependency_definition.description_long = self._GetConfigValue(
          config_parser, section_name, u'description_long')
      dependency_definition.description_short = self._GetConfigValue(
          config_parser, section_name, u'description_short')
      dependency_definition.disabled = self._GetConfigValue(
          config_parser, section_name, u'disabled')
      dependency_definition.dpkg_build_dependencies = self._GetConfigValue(
          config_parser, section_name, u'dpkg_build_dependencies')
      dependency_definition.dpkg_dependencies = self._GetConfigValue(
          config_parser, section_name, u'dpkg_dependencies')
      dependency_definition.dpkg_manual_install = self._GetConfigValue(
          config_parser, section_name, u'dpkg_manual_install')
      dependency_definition.dpkg_name = self._GetConfigValue(
          config_parser, section_name, u'dpkg_name')
      dependency_definition.download_url = self._GetConfigValue(
          config_parser, section_name, u'download_url')
      dependency_definition.homepage_url = self._GetConfigValue(
          config_parser, section_name, u'homepage_url')
      dependency_definition.maintainer = self._GetConfigValue(
          config_parser, section_name, u'maintainer')
      dependency_definition.patches = self._GetConfigValue(
          config_parser, section_name, u'patches')
      dependency_definition.setup_name = self._GetConfigValue(
          config_parser, section_name, u'setup_name')
      dependency_definition.version = self._GetConfigValue(
          config_parser, section_name, u'version')

      if dependency_definition.disabled is None:
        dependency_definition.disabled = []
      elif isinstance(dependency_definition.disabled, basestring):
        dependency_definition.disabled = dependency_definition.disabled.split(
            u',')

      if dependency_definition.dpkg_build_dependencies is None:
        dependency_definition.dpkg_build_dependencies = []
      elif isinstance(
          dependency_definition.dpkg_build_dependencies, basestring):
        dependency_definition.dpkg_build_dependencies = (
            dependency_definition.dpkg_build_dependencies.split(u','))

      if dependency_definition.dpkg_dependencies is None:
        dependency_definition.dpkg_dependencies = []
      elif isinstance(dependency_definition.dpkg_dependencies, basestring):
        dependency_definition.dpkg_dependencies = (
            dependency_definition.dpkg_dependencies.split(u','))

      if dependency_definition.patches is None:
        dependency_definition.patches = []
      elif isinstance(dependency_definition.patches, basestring):
        dependency_definition.patches = dependency_definition.patches.split(
            u',')

      # Need at minimum a name and a download URL.
      if dependency_definition.name and dependency_definition.download_url:
        yield dependency_definition

      dependency_definition.version = DependencyVersion(
          dependency_definition.version)
