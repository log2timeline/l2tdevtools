# -*- coding: utf-8 -*-
"""Writer for setup configuration and script files."""

import datetime
import glob
import logging
import os

from l2tdevtools.dependency_writers import interface


class PyprojectTomlWriter(interface.DependencyFileWriter):
  """Pyproject TOML script file writer."""

  PATH = os.path.join('pyproject.toml')

  _PROJECTS_WITH_PACKAGE_DATA = (
      'artifacts-kb', 'dfvfs', 'dfwinreg', 'dtformats', 'esedb-kb', 'mapi-kb',
      'olecf-kb', 'plaso', 'winreg-kb', 'winsps-kb')

  _TEMPLATE_DIRECTORY = os.path.join('data', 'templates', 'pyproject.toml')

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
    return super(PyprojectTomlWriter, self)._GenerateFromTemplate(
        template_filename, template_mappings)

  def Write(self):
    """Writes a pyproject.toml file."""
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

    # TODO: handle license-files

    maintainer_name, _, maintainer_email = (
        self._project_definition.maintainer.partition('<'))
    maintainer_name = maintainer_name.rstrip()
    maintainer_email = maintainer_email[:-1]

    python_module_name = self._project_definition.name

    if self._project_definition.name.endswith('-kb'):
      python_module_name = ''.join([python_module_name[:-3], 'rc'])

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

    readme_file = 'README.md'
    if not os.path.isfile(readme_file):
      readme_file = 'README'

    scripts_directory = 'scripts'
    if not os.path.isdir(scripts_directory):
      scripts_directory = 'tools'
    if not os.path.isdir(scripts_directory):
      scripts_directory = None

    if scripts_directory:
      if glob.glob(f'{scripts_directory:s}/[a-z]*.py'):
        logging.warning((
            'Scripts are not  supported by pyproject.toml, change them to '
            'console_scripts entry points.'))

    console_scripts_directory = os.path.join(python_module_name, 'scripts')
    if not os.path.isdir(console_scripts_directory):
      console_scripts_directory = None

    console_scripts = []
    if console_scripts_directory:
      console_scripts = glob.glob(f'{console_scripts_directory:s}/[a-z]*.py')

    date_time = datetime.datetime.now()
    version = date_time.strftime('%Y%m%d')

    template_mappings = {
        'description_short': (
            self._project_definition.description_short.rstrip(".")),
        'development_status': development_status,
        'maintainer_email': maintainer_email,
        'maintainer_name': maintainer_name,
        'python_module_name': python_module_name,
        'readme_file': readme_file,
        'version': version}

    file_content = []

    template_data = self._GenerateFromTemplate('header.toml', template_mappings)
    file_content.append(template_data)

    template_data = self._GenerateFromTemplate(
        'project.toml', template_mappings)
    file_content.append(template_data)

    python_dependencies = self._GetPyPIPythonDependencies()
    if python_dependencies:
      file_content.append('dependencies = [\n')
      for dependency in python_dependencies:
        dependency_string = str(dependency)
        file_content.append(f'    "{dependency_string:s}",\n')

      file_content.append(']\n')

    if console_scripts:
      file_content.append('\n')
      file_content.append('[project.scripts]\n')

      for console_script in sorted(console_scripts):
        console_script = console_script.replace('.py', '')
        module_name = console_script.replace(os.path.sep, '.')
        name = os.path.basename(console_script)
        file_content.append(f'{name:s} = "{module_name:s}:Main"\n')

    if self._project_definition.homepage_url:
      file_content.append('\n')
      file_content.append('[project.urls]\n')

      if os.path.isdir('docs'):
        url = f'https://{python_module_name:s}.readthedocs.io/en/latest'
        file_content.append(f'Documentation = "{url:s}"\n')

      url = self._project_definition.homepage_url
      file_content.append(f'Homepage = "{url:s}"\n')
      file_content.append(f'Repository = "{url:s}"\n')

    if package_data:
      file_content.append('\n')
      file_content.append('[tool.setuptools.package-data]\n')

      file_content.append(f'{python_module_name:s} = [\n')
      for data_file in sorted(package_data):
        if (self._project_definition.name == 'plaso' and
            data_file == 'data/*.yaml'):
          data_file = 'data/*.*'
        file_content.append(f'    "{data_file:s}",\n')

      file_content.append(']\n')

    template_data = self._GenerateFromTemplate(
        'setuptools.packages.toml', template_mappings)
    file_content.append(template_data)

    file_content = ''.join(file_content)

    with open(self.PATH, 'w', encoding='utf-8') as file_object:
      file_object.write(file_content)
