# -*- coding: utf-8 -*-
"""Writer for Sphinx build configuration and documentation files."""

import io
import os

from l2tdevtools.dependency_writers import interface


class SphinxBuildConfigurationWriter(interface.DependencyFileWriter):
  """Sphinx build configuration file writer."""

  _TEMPLATE_FILE = os.path.join('data', 'templates', 'docs', 'conf.py')

  PATH = os.path.join('docs', 'conf.py')

  def Write(self):
    """Writes a docs/conf.py file."""
    htmlhelp_basename = self._project_definition.name.replace('-', '')
    python_module_name = self._project_definition.name

    if self._project_definition.name.endswith('-kb'):
      htmlhelp_basename = htmlhelp_basename.replace('-', '')
      python_module_name = ''.join([python_module_name[:-3], 'rc'])

    template_mappings = {
        'htmlhelp_basename': htmlhelp_basename,
        'name_description': self._project_definition.name_description,
        'project_name': self._project_definition.name,
        'python_module_name': python_module_name}

    template_file = os.path.join(self._l2tdevtools_path, self._TEMPLATE_FILE)
    file_content = self._GenerateFromTemplate(template_file, template_mappings)

    with io.open(self.PATH, 'w', encoding='utf-8') as file_object:
      file_object.write(file_content)


class SphinxBuildRequirementsWriter(interface.DependencyFileWriter):
  """Sphinx build requirements file writer."""

  _TEMPLATE_FILE = os.path.join('data', 'templates', 'docs', 'requirements.txt')

  PATH = os.path.join('docs', 'requirements.txt')

  def Write(self):
    """Writes a docs/requirements.txt file."""
    template_mappings = {}

    template_file = os.path.join(self._l2tdevtools_path, self._TEMPLATE_FILE)
    file_content = self._GenerateFromTemplate(template_file, template_mappings)

    with io.open(self.PATH, 'w', encoding='utf-8') as file_object:
      file_object.write(file_content)
