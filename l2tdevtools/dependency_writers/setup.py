# -*- coding: utf-8 -*-
"""Writer for setup configuration and script files."""

import glob
import os

from l2tdevtools.dependency_writers import interface


class PyprojectTomlWriter(interface.DependencyFileWriter):
  """Pyproject TOML script file writer."""

  PATH = os.path.join('pyproject.toml')

  _TEMPLATE_FILE = os.path.join('data', 'templates', 'pyproject.toml')

  def Write(self):
    """Writes a pyproject.toml file."""
    path = os.path.join(self._l2tdevtools_path, self._TEMPLATE_FILE)
    with open(path, 'r', encoding='utf-8') as file_object:
      file_content = file_object.read()

    with open(self.PATH, 'w', encoding='utf-8') as file_object:
      file_object.write(file_content)


class SetupCfgWriter(interface.DependencyFileWriter):
  """Setup configuration file writer."""

  PATH = 'setup.cfg'

  _DOC_FILES = ('ACKNOWLEDGEMENTS', 'AUTHORS', 'LICENSE', 'README')

  _PROJECTS_WITH_PACKAGE_DATA = (
      'artifacts-kb', 'dfvfs', 'dfwinreg', 'dtformats', 'esedb-kb', 'olecf-kb',
      'plaso', 'winreg-kb', 'winsps-kb')

  _PROJECTS_WITH_SDIST_TEST_DATA = (
      'dfimagetools', 'dfvfs', 'dfwinreg', 'plaso', 'winevt-kb', 'winreg-kb',
      'winsps-kb')

  _TEMPLATE_DIRECTORY = os.path.join('data', 'templates', 'setup.cfg')

  def _DetermineSubmoduleLevels(self, python_module_name):
    """Determines the number of submodule levels.

    Args:
      python_module_name (str): name of the Python module.

    Return:
      int: number of submodule levels.
    """
    submodule_glob = python_module_name
    submodule_levels = 0

    while submodule_levels < 10:
      submodule_glob = f'{submodule_glob:s}/*'
      submodule_paths = [
          path for path in glob.glob(submodule_glob)
          if os.path.isdir(path) and os.path.basename(path) != '__pycache__']

      if not submodule_paths:
        break

      submodule_levels += 1

    return submodule_levels

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
    return super(SetupCfgWriter, self)._GenerateFromTemplate(
        template_filename, template_mappings)

  def Write(self):
    """Writes a setup.cfg file."""
    doc_files = [
        doc_file for doc_file in self._DOC_FILES if os.path.isfile(doc_file)]

    formatted_doc_files = [
        f'  {doc_file:s}' for doc_file in sorted(doc_files)]
    if formatted_doc_files:
      formatted_doc_files.insert(0, 'doc_files =')

    python3_dependencies = self._dependency_helper.GetRPMRequires()

    formatted_requires = [
          f'  {dependency:s}' for dependency in python3_dependencies]
    if formatted_requires:
      formatted_requires.insert(0, 'requires =')

    formatted_requires.append('')

    maintainer_name, _, maintainer_email = (
        self._project_definition.maintainer.partition('<'))
    maintainer_name = maintainer_name.rstrip()
    maintainer_email = maintainer_email[:-1]

    template_mappings = {
        'doc_files': '\n'.join(formatted_doc_files),
        'maintainer': self._project_definition.maintainer,
        'maintainer_email': maintainer_email,
        'maintainer_name': maintainer_name,
        'requires': '\n'.join(formatted_requires)}

    file_content = []

    template_data = self._GenerateFromTemplate('metadata', template_mappings)
    file_content.append(template_data)

    if self._project_definition.name in self._PROJECTS_WITH_SDIST_TEST_DATA:
      template_data = self._GenerateFromTemplate(
          'sdist_test_data', template_mappings)
      file_content.append(template_data)

    template_data = self._GenerateFromTemplate('bdist_rpm', template_mappings)
    file_content.append(template_data)

    template_data = self._GenerateFromTemplate('bdist_wheel', template_mappings)
    file_content.append(template_data)

    file_content = ''.join(file_content)

    with open(self.PATH, 'w', encoding='utf-8') as file_object:
      file_object.write(file_content)


class SetupPyWriter(interface.DependencyFileWriter):
  """Setup script file writer."""

  PATH = os.path.join('setup.py')

  _TEMPLATE_FILE = os.path.join('data', 'templates', 'setup.py')

  def Write(self):
    """Writes a setup.py file."""
    path = os.path.join(self._l2tdevtools_path, self._TEMPLATE_FILE)
    with open(path, 'r', encoding='utf-8') as file_object:
      file_content = file_object.read()

    with open(self.PATH, 'w', encoding='utf-8') as file_object:
      file_object.write(file_content)
