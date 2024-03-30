# -*- coding: utf-8 -*-
"""Writer for setup configuration and script files."""

import datetime
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
    description_long = ' '.join(
        self._project_definition.description_long.split('\n'))

    if self._project_definition.status == 'experimental':
      development_status = 'Development Status :: 2 - Pre-Alpha'
    elif self._project_definition.status == 'alpha':
      development_status = 'Development Status :: 3 - Alpha'
    elif self._project_definition.status == 'beta':
      development_status = 'Development Status :: 4 - Beta'
    elif self._project_definition.status == 'stable':
      development_status = 'Development Status :: 5 - Production/Stable'
    else:
      development_status = ''

    doc_files = [
        doc_file for doc_file in self._DOC_FILES if os.path.isfile(doc_file)]

    formatted_doc_files = [
        f'  {doc_file:s}' for doc_file in sorted(doc_files)]

    maintainer_name, _, maintainer_email = (
        self._project_definition.maintainer.partition('<'))
    maintainer_name = maintainer_name.rstrip()
    maintainer_email = maintainer_email[:-1]

    python_module_name = self._project_definition.name

    if self._project_definition.name.endswith('-kb'):
      python_module_name = ''.join([python_module_name[:-3], 'rc'])

    # TODO: handle data directory without yaml files.

    package_data = []
    for data_file in glob.glob(
        f'{python_module_name:s}/**/*.yaml', recursive=True):
      data_file_directory = os.path.dirname(
          data_file[len(f'{python_module_name:s}/'):])

      data_file = '*.yaml'
      if data_file_directory:
        data_file = '/'.join([data_file_directory, data_file])

      if data_file not in package_data:
        package_data.append(data_file)

    formatted_package_data = [
        f'  {data_file:s}' for data_file in sorted(package_data)]

    scripts_directory = 'scripts'
    if not os.path.isdir(scripts_directory):
      scripts_directory = 'tools'
    if not os.path.isdir(scripts_directory):
      scripts_directory = None

    scripts = []
    if scripts_directory:
      scripts = glob.glob(f'{scripts_directory:s}/[a-z]*.py')

    formatted_scripts = [
        f'  {script:s}' for script in sorted(scripts)]

    console_scripts_directory = os.path.join(python_module_name, 'scripts')
    if not os.path.isdir(console_scripts_directory):
      console_scripts_directory = None

    console_scripts = []
    if console_scripts_directory:
      console_scripts = glob.glob(f'{console_scripts_directory:s}/[a-z]*.py')

    entry_points_console_scripts = []
    for console_script in sorted(console_scripts):
      console_script = console_script.replace('.py', '')
      module_name = console_script.replace(os.path.sep, '.')
      name = os.path.basename(console_script)
      entry_points_console_scripts.append(f'  {name:s} = {module_name:s}:Main')

    date_time = datetime.datetime.now()
    version = date_time.strftime('%Y%m%d')

    template_mappings = {
        'console_scripts': '\n'.join(entry_points_console_scripts),
        'description_long': description_long,
        'description_short': self._project_definition.description_short,
        'development_status': development_status,
        'doc_files': '\n'.join(formatted_doc_files),
        'homepage_url': self._project_definition.homepage_url,
        'maintainer': self._project_definition.maintainer,
        'maintainer_email': maintainer_email,
        'maintainer_name': maintainer_name,
        'package_data': '\n'.join(formatted_package_data),
        'python_module_name': python_module_name,
        'scripts': '\n'.join(formatted_scripts),
        'version': version}

    file_content = []

    template_data = self._GenerateFromTemplate('metadata', template_mappings)
    file_content.append(template_data)

    if scripts:
      template_data = self._GenerateFromTemplate(
          'options_scripts', template_mappings)
      file_content.append(template_data)

    if package_data:
      template_data = self._GenerateFromTemplate(
          'options_package_data', template_mappings)
      file_content.append(template_data)

    template_data = self._GenerateFromTemplate(
        'options_packages_find', template_mappings)
    file_content.append(template_data)

    if entry_points_console_scripts:
      template_data = self._GenerateFromTemplate(
          'options_entry_points', template_mappings)
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
