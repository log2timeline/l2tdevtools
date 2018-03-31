# -*- coding: utf-8 -*-
"""Helper for writing files that contain dependency information."""

from __future__ import unicode_literals

import abc
import string


class DependencyFileWriter(object):
  """Base class for dependency file writers."""

  def __init__(self, l2tdevtools_path, project_definition, dependency_helper):
    """Initializes a dependency file writer.

    Args:
      l2tdevtools_path (str): path to l2tdevtools.
      project_definition (ProjectDefinition): project definition.
      dependency_helper (DependencyHelper): dependency helper.
    """
    super(DependencyFileWriter, self).__init__()
    self._dependency_helper = dependency_helper
    self._l2tdevtools_path = l2tdevtools_path
    self._project_definition = project_definition

  def _ReadTemplateFile(self, filename):
    """Reads a template string from file.

    Args:
      filename (str): name of the file containing the template string.

    Returns:
      string.Template: template string.
    """
    with open(filename, 'rb') as file_object:
      file_data = file_object.read()

    return string.Template(file_data)

  def _GenerateFromTemplate(self, template_filename, template_mappings):
    """Generates file context based on a template file.

    Args:
      template_filename (str): path of the template file.
      template_mappings (dict[str, str]): template mappings, where the key
          maps to the name of a template variable.

    Returns:
      str: output based on the template string.

    Raises:
      RuntimeError: if the template cannot be formatted.
    """
    template_string = self._ReadTemplateFile(template_filename)

    try:
      return template_string.substitute(template_mappings)

    except (KeyError, ValueError) as exception:
      raise RuntimeError(
          'Unable to format template: {0:s} with error: {1!s}'.format(
              template_filename, exception))

  @abc.abstractmethod
  def Write(self):
    """Writes the file or files produced by the file writer."""
