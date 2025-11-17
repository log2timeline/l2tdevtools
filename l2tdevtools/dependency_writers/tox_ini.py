# -*- coding: utf-8 -*-
"""Writer for tox.ini files."""

import glob
import os

from l2tdevtools.dependency_writers import interface


class ToxIniWriter(interface.DependencyFileWriter):
  """Tox.ini file writer."""

  _TEMPLATE_DIRECTORY = os.path.join('data', 'templates', 'tox.ini')

  PATH = 'tox.ini'

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
    template_filename = os.path.join(
        self._l2tdevtools_path, self._TEMPLATE_DIRECTORY, template_filename)
    return super(ToxIniWriter, self)._GenerateFromTemplate(
        template_filename, template_mappings)

  def Write(self):
    """Writes a tox.ini file."""
    python_module_name = self._project_definition.name

    if self._project_definition.name.endswith('-kb'):
      python_module_name = ''.join([python_module_name[:-3], 'rc'])

    paths_to_lint_python = []
    paths_to_lint_yaml = []

    if os.path.isdir(python_module_name):
      paths_to_lint_python.append(python_module_name)

      if glob.glob(os.path.join(
          python_module_name, '**', '*.yaml'), recursive=True):
        paths_to_lint_yaml.append(python_module_name)

    if os.path.isdir('data'):
      if glob.glob(os.path.join('data', '**', '*.yaml'), recursive=True):
        paths_to_lint_yaml.append('data')

    if os.path.isfile('setup.py'):
      paths_to_lint_python.append('setup.py')

    if os.path.isdir('scripts'):
      paths_to_lint_python.append('scripts')

    if os.path.isdir('test_data'):
      if glob.glob(os.path.join('test_data', '**', '*.yaml'), recursive=True):
        paths_to_lint_yaml.append('test_data')

    if os.path.isdir('tests'):
      paths_to_lint_python.append('tests')

      if glob.glob(os.path.join('tests', '**', '*.yaml'), recursive=True):
        paths_to_lint_yaml.append('tests')

    if os.path.isdir('tools'):
      paths_to_lint_python.append('tools')

    envlist = ['py3{10,11,12,13,14}', 'coverage', 'docformatter']
    if os.path.isdir('docs'):
      envlist.append('docs')

    envlist.extend(['lint', 'wheel'])

    template_mappings = {
        'envlist': ','.join(envlist),
        'paths_to_lint_python': ' '.join(sorted(paths_to_lint_python)),
        'paths_to_lint_yaml': ' '.join(sorted(paths_to_lint_yaml)),
        'project_name': self._project_definition.name,
        'python_module_name': python_module_name}

    file_content = []

    template_data = self._GenerateFromTemplate('header', template_mappings)
    file_content.append(template_data)

    if os.path.isdir('docs'):
      template_data = self._GenerateFromTemplate(
          'testenv_docs', template_mappings)
      file_content.append(template_data)

    if paths_to_lint_yaml:
      template_name = 'testenv_lint-with_yaml'
    else:
      template_name = 'testenv_lint'

    template_data = self._GenerateFromTemplate(
        template_name, template_mappings)
    file_content.append(template_data)

    file_content = ''.join(file_content)

    with open(self.PATH, 'w', encoding='utf-8') as file_object:
      file_object.write(file_content)
