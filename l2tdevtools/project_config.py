# -*- coding: utf-8 -*-
"""Helper for project configuration."""

from __future__ import print_function
from __future__ import unicode_literals

import configparser


class ProjectDefinition(object):
  """Project definition.

  Attributes:
    description_long (str): long description.
    description_short (str): short description.
    git_url (str): URL of the git repository.
    homepage_url (str): URL of the homepage.
    maintainer (str): maintainer.
    name (str): name of the project.
    name_description (str): name of the project to use in descriptions.
    status (str): development status of the projects, such as "alpha" or "beta".
  """

  def __init__(self):
    """Initializes a project configuration."""
    super(ProjectDefinition, self).__init__()
    self.description_long = None
    self.description_short = None
    self.git_url = None
    self.homepage_url = None
    self.maintainer = None
    self.name = None
    self.name_description = None
    self.status = 'alpha'


class ProjectDefinitionReader(object):
  """Project definition reader."""

  _VALUE_NAMES = frozenset([
      'description_long',
      'description_short',
      'git_url',
      'homepage_url',
      'maintainer',
      'name',
      'name_description',
      'status'])

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

    Returns:
      ProjectDefinition: project definition.
    """
    config_parser = configparser.ConfigParser(interpolation=None)
    config_parser.read_file(file_object)

    project_definition = ProjectDefinition()
    for value_name in self._VALUE_NAMES:
      value = self._GetConfigValue(config_parser, 'project', value_name)
      setattr(project_definition, value_name, value)

    return project_definition
