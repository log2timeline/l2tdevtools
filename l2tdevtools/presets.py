# -*- coding: utf-8 -*-
"""Project preset definitions."""

from __future__ import unicode_literals

import sys

try:
  import ConfigParser as configparser
except ImportError:
  import configparser  # pylint: disable=import-error

from l2tdevtools import py2to3


class PresetDefinition(object):
  """Class that implements a preset definition.

  Attributes:
    name (str): name of the dependency.
    project_names (list[str]): project names.
  """

  def __init__(self, name):
    """Initializes the preset definition.

    Args:
      name (str): name of the preset.
    """
    super(PresetDefinition, self).__init__()
    self.name = name
    self.project_names = None


class PresetDefinitionReader(object):
  """Preset definition reader."""

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
    """Reads preset definitions.

    Args:
      file_object (file): file-like object to read from.

    Yields:
      PresetDefinition: preset definitions.
    """
    # TODO: replace by:
    # config_parser = configparser. ConfigParser(interpolation=None)
    config_parser = configparser.RawConfigParser()

    if sys.version_info[0] < 3:
      config_parser.readfp(file_object)  # pylint: disable=deprecated-method
    else:
      config_parser.read_file(file_object)

    for section_name in config_parser.sections():
      preset_definition = PresetDefinition(section_name)

      preset_definition.project_names = self._GetConfigValue(
          config_parser, section_name, 'projects')

      if preset_definition.project_names is None:
        preset_definition.project_names = []
      elif isinstance(
          preset_definition.project_names, py2to3.STRING_TYPES):
        preset_definition.project_names = (
            preset_definition.project_names.split(','))

      # Need at minimum a name.
      if preset_definition.name:
        yield preset_definition
