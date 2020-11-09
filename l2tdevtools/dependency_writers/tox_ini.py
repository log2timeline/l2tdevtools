# -*- coding: utf-8 -*-
"""Writer for tox.ini files."""

from __future__ import unicode_literals

import io
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
    paths_to_lint = []

    if os.path.isdir(self._project_definition.name):
      paths_to_lint.append(self._project_definition.name)

    if os.path.isdir('scripts'):
      paths_to_lint.append('scripts')
    elif os.path.isdir('tools'):
      paths_to_lint.append('tools')

    if os.path.isdir('tests'):
      paths_to_lint.append('tests')

      envlist = 'py3{6,7,8,9},coverage,docs,pylint'
    else:
      envlist = 'py3{6,7,8,9},coverage,pylint'

    template_mappings = {
        'envlist': envlist,
        'paths_to_lint': ' '.join(sorted(paths_to_lint)),
        'project_name': self._project_definition.name}

    file_content = []

    template_data = self._GenerateFromTemplate('header', template_mappings)
    file_content.append(template_data)

    if os.path.isdir('docs'):
      template_data = self._GenerateFromTemplate(
          'testenv_docs', template_mappings)
      file_content.append(template_data)

    template_data = self._GenerateFromTemplate(
        'testenv_pylint', template_mappings)
    file_content.append(template_data)

    file_content = ''.join(file_content)

    with io.open(self.PATH, 'w', encoding='utf-8') as file_object:
      file_object.write(file_content)
