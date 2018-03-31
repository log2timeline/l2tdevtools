#!/usr/bin/env python
# -*- coding: utf-8 -*-
# pylint: disable=invalid-name
"""Script to update the dependencies in various configuration files."""

from __future__ import unicode_literals

import string
import os

from l2tdevtools import dependencies
from l2tdevtools import project_config


# pylint: disable=redefined-outer-name


class DependencyFileWriter(object):
  """Dependency file writer."""

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


class AppveyorYmlWriter(DependencyFileWriter):
  """Appveyor.yml file writer."""

  PATH = os.path.join('appveyor.yml')

  _VERSION_SQLITE = '3220000'

  _UPGRADE_PIP = (
      '- cmd: "%PYTHON%\\\\python.exe -m pip install --upgrade pip"')

  _INSTALL_PYWIN32_WMI = (
      '- cmd: "%PYTHON%\\\\Scripts\\\\pip.exe install pywin32 WMI"')

  _POST_INSTALL_PYWIN32 = (
      '- cmd: "%PYTHON%\\\\python.exe %PYTHON%\\\\Scripts\\\\'
      'pywin32_postinstall.py -install"')

  _URL_L2TDEVTOOLS = 'https://github.com/log2timeline/l2tdevtools.git'

  _DOWNLOAD_L2TDEVTOOLS = (
      '- cmd: git clone {0:s} ..\\l2tdevtools'.format(
          _URL_L2TDEVTOOLS))

  _L2TDEVTOOLS = [
      _UPGRADE_PIP,
      _INSTALL_PYWIN32_WMI,
      _POST_INSTALL_PYWIN32,
      _DOWNLOAD_L2TDEVTOOLS]

  _FILE_HEADER = [
      'environment:',
      '  matrix:',
      '  - TARGET: python27',
      '    PYTHON: "C:\\\\Python27"',
      '  - TARGET: python36',
      '    PYTHON: "C:\\\\Python36"',
      '']

  _ALLOW_FAILURES = [
      'matrix:',
      '  allow_failures:',
      '  - TARGET: python36',
      '']

  _INSTALL = [
      'install:',
      ('- cmd: \'"C:\\Program Files\\Microsoft SDKs\\Windows\\v7.1\\Bin\\'
       'SetEnv.cmd" /x86 /release\'')]

  _SET_TLS_VERSION = (
      '- ps: "[System.Net.ServicePointManager]::SecurityProtocol = '
      '[System.Net.SecurityProtocolType]::Tls12"')

  _DOWNLOAD_SQLITE = (
      '- ps: (new-object net.webclient).DownloadFile('
      '\'https://www.sqlite.org/2018/sqlite-dll-win32-x86-{0:s}.zip\', '
      '\'C:\\Projects\\sqlite-dll-win32-x86-{0:s}.zip\')').format(
          _VERSION_SQLITE)

  _EXTRACT_SQLITE = (
      '- ps: $Output = Invoke-Expression -Command '
      '"& \'C:\\\\Program Files\\\\7-Zip\\\\7z.exe\' -y '
      '-oC:\\\\Projects\\\\ x C:\\\\Projects\\\\'
      'sqlite-dll-win32-x86-{0:s}.zip 2>&1"').format(_VERSION_SQLITE)

  _INSTALL_SQLITE = (
      '- cmd: copy C:\\Projects\\sqlite3.dll C:\\Python27\\DLLs\\')

  _SQLITE = [
      _SET_TLS_VERSION,
      _DOWNLOAD_SQLITE,
      _EXTRACT_SQLITE,
      _INSTALL_SQLITE]

  _L2TDEVTOOLS_UPDATE = '\n'.join([
      '- cmd: if [%TARGET%]==[{0:s}] (',
      '    mkdir dependencies &&',
      '    set PYTHONPATH=..\\l2tdevtools &&',
      ('    "%PYTHON%\\\\python.exe" ..\\l2tdevtools\\tools\\update.py '
       '--download-directory dependencies --machine-type x86 '
       '--msi-targetdir "%PYTHON%" --track dev {1:s} )')])

  _FILE_FOOTER = [
      '',
      'build: off',
      '',
      'test_script:',
      '- "%PYTHON%\\\\python.exe run_tests.py"',
      '']

  def Write(self):
    """Writes an appveyor.yml file."""
    file_content = []
    file_content.extend(self._FILE_HEADER)

    if self._project_definition.name in ('dfvfs', 'l2tpreg', 'plaso'):
      file_content.extend(self._ALLOW_FAILURES)

    file_content.extend(self._INSTALL)

    python2_dependencies = self._dependency_helper.GetL2TBinaries(
        python_version=2)

    if 'pysqlite' in python2_dependencies:
      file_content.extend(self._SQLITE)

    file_content.extend(self._L2TDEVTOOLS)

    python2_dependencies.extend(['funcsigs', 'mock', 'pbr'])

    if 'six' not in python2_dependencies:
      python2_dependencies.append('six')

    if self._project_definition.name == 'artifacts':
      python2_dependencies.append('yapf')

    if 'backports.lzma' in python2_dependencies:
      python2_dependencies.remove('backports.lzma')

    python2_dependencies = ' '.join(sorted(python2_dependencies))
    l2tdevtools_update = self._L2TDEVTOOLS_UPDATE.format(
        'python27', python2_dependencies)
    file_content.append(l2tdevtools_update)

    python3_dependencies = self._dependency_helper.GetL2TBinaries(
        python_version=3)

    python3_dependencies.extend(['funcsigs', 'mock', 'pbr'])

    if 'six' not in python3_dependencies:
      python3_dependencies.append('six')

    python3_dependencies = ' '.join(sorted(python3_dependencies))
    l2tdevtools_update = self._L2TDEVTOOLS_UPDATE.format(
        'python36', python3_dependencies)
    file_content.append(l2tdevtools_update)

    file_content.extend(self._FILE_FOOTER)

    file_content = '\n'.join(file_content)
    file_content = file_content.encode('utf-8')

    with open(self.PATH, 'wb') as file_object:
      file_object.write(file_content)


class DependenciesPyWriter(DependencyFileWriter):
  """Dependencies.py file writer."""

  _TEMPLATE_FILE = os.path.join('data', 'templates', 'dependencies.py')

  PATH = os.path.join('plaso', 'dependencies.py')

  def Write(self):
    """Writes a dependencies.py file."""
    dependencies = sorted(
        self._dependency_helper.dependencies.values(),
        key=lambda dependency: dependency.name.lower())

    python_dependencies = []
    for dependency in dependencies:
      if dependency.maximum_version:
        maximum_version = '\'{0:s}\''.format(dependency.maximum_version)
      else:
        maximum_version = 'None'

      python_dependency = (
          '    \'{0:s}\': (\'{1:s}\', \'{2:s}\', {3:s}, {4!s})').format(
              dependency.name, dependency.version_property or '',
              dependency.minimum_version or '', maximum_version,
              not dependency.is_optional)

      python_dependencies.append(python_dependency)

    python_dependencies = ',\n'.join(python_dependencies)

    template_mappings = {'python_dependencies': python_dependencies}

    template_file = os.path.join(self._l2tdevtools_path, self._TEMPLATE_FILE)
    file_content = self._GenerateFromTemplate(template_file, template_mappings)

    file_content = file_content.encode('utf-8')

    with open(self.PATH, 'wb') as file_object:
      file_object.write(file_content)


class DPKGControlWriter(DependencyFileWriter):
  """Dpkg control file writer."""

  PATH = os.path.join('config', 'dpkg', 'control')

  _PYTHON2_FILE_HEADER = [
      'Source: {project_name:s}',
      'Section: python',
      'Priority: extra',
      'Maintainer: {maintainer:s}',
      ('Build-Depends: debhelper (>= 9), python-all (>= 2.7~), '
       'python-setuptools'),
      'Standards-Version: 3.9.5',
      'X-Python-Version: >= 2.7',
      'Homepage: {homepage_url:s}',
      '']

  _PYTHON3_FILE_HEADER = [
      'Source: {project_name:s}',
      'Section: python',
      'Priority: extra',
      'Maintainer: {maintainer:s}',
      ('Build-Depends: debhelper (>= 9), python-all (>= 2.7~), '
       'python-setuptools, python3-all (>= 3.4~), python3-setuptools'),
      'Standards-Version: 3.9.5',
      'X-Python-Version: >= 2.7',
      'X-Python3-Version: >= 3.4',
      'Homepage: {homepage_url:s}',
      '']

  _DATA_PACKAGE = [
      'Package: {project_name:s}-data',
      'Architecture: all',
      'Depends: ${{misc:Depends}}',
      'Description: Data files for {name_description:s}',
      '{description_long:s}',
      '']

  _PYTHON2_PACKAGE = [
      'Package: python-{project_name:s}',
      'Architecture: all',
      ('Depends: {python2_dependencies:s}'
       '${{python:Depends}}, ${{misc:Depends}}'),
      'Description: Python 2 module of {name_description:s}',
      '{description_long:s}',
      '']

  _PYTHON3_PACKAGE = [
      'Package: python3-{project_name:s}',
      'Architecture: all',
      ('Depends: {python3_dependencies:s}'
       '${{python3:Depends}}, ${{misc:Depends}}'),
      'Description: Python 3 module of {name_description:s}',
      '{description_long:s}',
      '']

  _TOOLS_PACKAGE = [
      'Package: {project_name:s}-tools',
      'Architecture: all',
      ('Depends: python-{project_name:s}, python (>= 2.7~), '
       '${{python:Depends}}, ${{misc:Depends}}'),
      'Description: Tools of {name_description:s}',
      '{description_long:s}',
      '']

  def Write(self):
    """Writes a dpkg control file."""
    file_content = []

    if self._project_definition.python2_only:
      file_content.extend(self._PYTHON2_FILE_HEADER)
    else:
      file_content.extend(self._PYTHON3_FILE_HEADER)

    data_dependency = ''
    if os.path.isdir('data'):
      data_dependency = '{0:s}-data'.format(self._project_definition.name)

      file_content.extend(self._DATA_PACKAGE)

    file_content.extend(self._PYTHON2_PACKAGE)

    if not self._project_definition.python2_only:
      file_content.extend(self._PYTHON3_PACKAGE)

    if os.path.isdir('scripts') or os.path.isdir('tools'):
      file_content.extend(self._TOOLS_PACKAGE)

    description_long = self._project_definition.description_long
    description_long = '\n'.join([
        ' {0:s}'.format(line) for line in description_long.split('\n')])

    python2_dependencies = self._dependency_helper.GetDPKGDepends(
        python_version=2)

    if data_dependency:
      python2_dependencies.insert(0, data_dependency)

    python2_dependencies = ', '.join(python2_dependencies)
    if python2_dependencies:
      python2_dependencies = '{0:s}, '.format(python2_dependencies)

    python3_dependencies = self._dependency_helper.GetDPKGDepends(
        python_version=3)

    if data_dependency:
      python3_dependencies.insert(0, data_dependency)

    python3_dependencies = ', '.join(python3_dependencies)
    if python3_dependencies:
      python3_dependencies = '{0:s}, '.format(python3_dependencies)

    template_mappings = {
        'description_long': description_long,
        'description_short': self._project_definition.description_short,
        'homepage_url': self._project_definition.homepage_url,
        'maintainer': self._project_definition.maintainer,
        'name_description': self._project_definition.name_description,
        'project_name': self._project_definition.name,
        'python2_dependencies': python2_dependencies,
        'python3_dependencies': python3_dependencies}

    file_content = '\n'.join(file_content)
    file_content = file_content.format(**template_mappings)

    file_content = file_content.encode('utf-8')

    with open(self.PATH, 'wb') as file_object:
      file_object.write(file_content)


class GIFTCOPRInstallScriptWriter(DependencyFileWriter):
  """GIFT COPR installation script file writer."""

  PATH = os.path.join('config', 'linux', 'gift_copr_install.sh')

  _FILE_HEADER = [
      '#!/usr/bin/env bash',
      '#',
      ('# This file is generated by l2tdevtools update-dependencies.py any '
       'dependency'),
      '# related changes should be made in dependencies.ini.',
      '',
      '# Exit on error.',
      'set -e',
      '',
      ('# Dependencies for running {project_name:s}, alphabetized, one per '
       'line.'),
      ('# This should not include packages only required for testing or '
       'development.')]

  _ADDITIONAL_DEPENDENCIES = [
      '',
      ('# Additional dependencies for running {project_name:s} tests, '
       'alphabetized,'),
      '# one per line.',
      'TEST_DEPENDENCIES="python-mock";',
      '',
      ('# Additional dependencies for doing {project_name:s} development, '
       'alphabetized,'),
      '# one per line.',
      'DEVELOPMENT_DEPENDENCIES="python-sphinx',
      '                          pylint";',
      '',
      ('# Additional dependencies for doing {project_name:s} debugging, '
       'alphabetized,'),
      '# one per line.']

  _FILE_FOOTER = [
      '',
      'sudo dnf install dnf-plugins-core',
      'sudo dnf copr enable @gift/dev',
      'sudo dnf install -y ${{PYTHON2_DEPENDENCIES}}',
      '',
      'if [[ "$*" =~ "include-debug" ]]; then',
      '    sudo dnf install -y ${{DEBUG_DEPENDENCIES}}',
      'fi',
      '',
      'if [[ "$*" =~ "include-development" ]]; then',
      '    sudo dnf install -y ${{DEVELOPMENT_DEPENDENCIES}}',
      'fi',
      '',
      'if [[ "$*" =~ "include-test" ]]; then',
      '    sudo dnf install -y ${{TEST_DEPENDENCIES}}',
      'fi',
      '']

  def Write(self):
    """Writes a gift_copr_install.sh file."""
    file_content = []
    file_content.extend(self._FILE_HEADER)

    python2_dependencies = self._dependency_helper.GetRPMRequires(
        exclude_version=True, python_version=2)

    libyal_dependencies = []
    for index, dependency in enumerate(python2_dependencies):
      if index == 0:
        file_content.append('PYTHON2_DEPENDENCIES="{0:s}'.format(dependency))
      elif index + 1 == len(python2_dependencies):
        file_content.append('                      {0:s}";'.format(dependency))
      else:
        file_content.append('                      {0:s}'.format(dependency))

      if dependency.startswith('lib') and dependency.endswith('-python'):
        dependency, _, _ = dependency.partition('-')
        libyal_dependencies.append(dependency)

    file_content.extend(self._ADDITIONAL_DEPENDENCIES)

    for index, dependency in enumerate(libyal_dependencies):
      if index == 0:
        file_content.append('DEBUG_DEPENDENCIES="{0:s}-debuginfo'.format(
            dependency))
      elif index + 1 == len(libyal_dependencies):
        file_content.append('                    {0:s}-debuginfo";'.format(
            dependency))
      else:
        file_content.append('                    {0:s}-debuginfo'.format(
            dependency))

    file_content.extend(self._FILE_FOOTER)

    template_mappings = {'project_name': self._project_definition.name}

    file_content = '\n'.join(file_content)
    file_content = file_content.format(**template_mappings)

    file_content = file_content.encode('utf-8')

    with open(self.PATH, 'wb') as file_object:
      file_object.write(file_content)


class GIFTPPAInstallScriptWriter(DependencyFileWriter):
  """GIFT PPA installation script file writer."""

  PATH = os.path.join('config', 'linux', 'gift_ppa_install.sh')

  _FILE_HEADER = [
      '#!/usr/bin/env bash',
      '#',
      ('# This file is generated by l2tdevtools update-dependencies.py any '
       'dependency'),
      '# related changes should be made in dependencies.ini.',
      '',
      '# Exit on error.',
      'set -e',
      '',
      ('# Dependencies for running {project_name:s}, alphabetized, one per '
       'line.'),
      ('# This should not include packages only required for testing or '
       'development.')]

  _ADDITIONAL_DEPENDENCIES = [
      '',
      ('# Additional dependencies for running {project_name:s} tests, '
       'alphabetized,'),
      '# one per line.',
      'TEST_DEPENDENCIES="python-mock";',
      '',
      ('# Additional dependencies for doing {project_name:s} development, '
       'alphabetized,'),
      '# one per line.',
      'DEVELOPMENT_DEPENDENCIES="python-sphinx',
      '                          pylint";']

  _DEBUG_DEPENDENCIES = [
      '',
      ('# Additional dependencies for doing {project_name:s} debugging, '
       'alphabetized,'),
      '# one per line.']

  _FILE_FOOTER = [
      '',
      'sudo add-apt-repository ppa:gift/dev -y',
      'sudo apt-get update -q',
      'sudo apt-get install -y ${{PYTHON2_DEPENDENCIES}}']

  _FILE_FOOTER_DEBUG_DEPENDENCIES = [
      '',
      'if [[ "$*" =~ "include-debug" ]]; then',
      '    sudo apt-get install -y ${{DEBUG_DEPENDENCIES}}',
      'fi']

  _FILE_FOOTER_DEVELOPMENT_DEPENDENCIES = [
      '',
      'if [[ "$*" =~ "include-development" ]]; then',
      '    sudo apt-get install -y ${{DEVELOPMENT_DEPENDENCIES}}',
      'fi']

  _FILE_FOOTER_TEST_DEPENDENCIES = [
      '',
      'if [[ "$*" =~ "include-test" ]]; then',
      '    sudo apt-get install -y ${{TEST_DEPENDENCIES}}',
      'fi',
      '']

  def Write(self):
    """Writes a gift_ppa_install.sh file."""
    file_content = []
    file_content.extend(self._FILE_HEADER)

    python2_dependencies = self._dependency_helper.GetDPKGDepends(
        exclude_version=True, python_version=2)

    libyal_dependencies = []
    for index, dependency in enumerate(python2_dependencies):
      if index == 0:
        file_content.append('PYTHON2_DEPENDENCIES="{0:s}'.format(dependency))
      elif index + 1 == len(python2_dependencies):
        file_content.append('                      {0:s}";'.format(dependency))
      else:
        file_content.append('                      {0:s}'.format(dependency))

      if dependency.startswith('lib') and dependency.endswith('-python'):
        dependency, _, _ = dependency.partition('-')
        libyal_dependencies.append(dependency)

    file_content.extend(self._ADDITIONAL_DEPENDENCIES)

    debug_dependencies = []
    for index, dependency in enumerate(libyal_dependencies):
      debug_dependencies.append('{0:s}-dbg'.format(dependency))
      debug_dependencies.append('{0:s}-python-dbg'.format(dependency))

    if self._project_definition.name == 'plaso':
      debug_dependencies.append('python-guppy')

    if debug_dependencies:
      file_content.extend(self._DEBUG_DEPENDENCIES)

      for index, dependency in enumerate(debug_dependencies):
        if index == 0:
          file_content.append('DEBUG_DEPENDENCIES="{0:s}'.format(dependency))
        elif index + 1 == len(debug_dependencies):
          file_content.append('                    {0:s}";'.format(dependency))
        else:
          file_content.append('                    {0:s}'.format(dependency))

    file_content.extend(self._FILE_FOOTER)

    if debug_dependencies:
      file_content.extend(self._FILE_FOOTER_DEBUG_DEPENDENCIES)

    file_content.extend(self._FILE_FOOTER_DEVELOPMENT_DEPENDENCIES)
    file_content.extend(self._FILE_FOOTER_TEST_DEPENDENCIES)

    template_mappings = {'project_name': self._project_definition.name}

    file_content = '\n'.join(file_content)
    file_content = file_content.format(**template_mappings)

    file_content = file_content.encode('utf-8')

    with open(self.PATH, 'wb') as file_object:
      file_object.write(file_content)


class PylintRcWriter(DependencyFileWriter):
  """Pylint.rc file writer."""

  _TEMPLATE_FILE = os.path.join('data', 'templates', '.pylintrc')

  PATH = '.pylintrc'

  def Write(self):
    """Writes a .travis.yml file."""
    dependencies = self._dependency_helper.GetPylintRcExtensionPkgs()

    template_mappings = {'extension_pkg_whitelist': ','.join(dependencies)}

    template_file = os.path.join(self._l2tdevtools_path, self._TEMPLATE_FILE)
    file_content = self._GenerateFromTemplate(template_file, template_mappings)

    file_content = file_content.encode('utf-8')

    with open(self.PATH, 'wb') as file_object:
      file_object.write(file_content)


class RequirementsWriter(DependencyFileWriter):
  """Requirements.txt file writer."""

  PATH = 'requirements.txt'

  _FILE_HEADER = ['pip >= 7.0.0']

  def Write(self):
    """Writes a requirements.txt file."""
    file_content = []
    file_content.extend(self._FILE_HEADER)

    dependencies = self._dependency_helper.GetInstallRequires()
    for dependency in dependencies:
      file_content.append('{0:s}'.format(dependency))

    file_content.append('')

    file_content = '\n'.join(file_content)
    file_content = file_content.encode('utf-8')

    with open(self.PATH, 'wb') as file_object:
      file_object.write(file_content)


class SetupCfgWriter(DependencyFileWriter):
  """Setup.cfg file writer."""

  PATH = 'setup.cfg'

  _SDIST = [
      '[sdist]',
      'template = MANIFEST.in',
      'manifest = MANIFEST',
      '',
      '[sdist_test_data]',
      'template = MANIFEST.test_data.in',
      'manifest = MANIFEST.test_data',
      '']

  _BDIST_RPM = [
      '[bdist_rpm]',
      'release = 1',
      'packager = {maintainer:s}']

  def Write(self):
    """Writes a setup.cfg file."""
    file_content = []

    if self._project_definition.name in ('dfvfs', 'l2tpreg', 'plaso'):
      file_content.extend(self._SDIST)

    file_content.extend(self._BDIST_RPM)

    doc_files = ['AUTHORS', 'LICENSE', 'README']

    if os.path.isfile('ACKNOWLEDGEMENTS'):
      doc_files.append('ACKNOWLEDGEMENTS')

    for index, doc_file in enumerate(sorted(doc_files)):
      if index == 0:
        file_content.append('doc_files = {0:s}'.format(doc_file))
      else:
        file_content.append('            {0:s}'.format(doc_file))

    file_content.append('build_requires = python-setuptools')

    python2_dependencies = self._dependency_helper.GetRPMRequires(
        python_version=2)

    for index, dependency in enumerate(python2_dependencies):
      if index == 0:
        file_content.append('requires = {0:s}'.format(dependency))
      else:
        file_content.append('           {0:s}'.format(dependency))

    file_content.append('')

    template_mappings = {'maintainer': self._project_definition.maintainer}

    file_content = '\n'.join(file_content)
    file_content = file_content.format(**template_mappings)
    file_content = file_content.encode('utf-8')

    with open(self.PATH, 'wb') as file_object:
      file_object.write(file_content)


class TravisInstallScriptWriter(DependencyFileWriter):
  """Travis-CI install.sh file writer."""

  PATH = os.path.join('config', 'travis', 'install.sh')

  _URL_L2TDEVTOOLS = 'https://github.com/log2timeline/l2tdevtools.git'

  _FILE_HEADER = [
      '#!/bin/bash',
      '#',
      '# Script to set up Travis-CI test VM.',
      '#',
      ('# This file is generated by l2tdevtools update-dependencies.py any '
       'dependency'),
      '# related changes should be made in dependencies.ini.',
      '']

  _FILE_FOOTER = [
      '',
      '# Exit on error.',
      'set -e;',
      '',
      'if test ${TRAVIS_OS_NAME} = "osx";',
      'then',
      '\tgit clone https://github.com/log2timeline/l2tbinaries.git -b dev;',
      '',
      '\tmv l2tbinaries ../;',
      '',
      '\tfor PACKAGE in ${L2TBINARIES_DEPENDENCIES};',
      '\tdo',
      '\t\techo "Installing: ${PACKAGE}";',
      '\t\tsudo /usr/bin/hdiutil attach ../l2tbinaries/macos/${PACKAGE}-*.dmg;',
      ('\t\tsudo /usr/sbin/installer -target / -pkg '
       '/Volumes/${PACKAGE}-*.pkg/${PACKAGE}-*.pkg;'),
      '\t\tsudo /usr/bin/hdiutil detach /Volumes/${PACKAGE}-*.pkg',
      '\tdone',
      '',
      '\tfor PACKAGE in ${L2TBINARIES_TEST_DEPENDENCIES};',
      '\tdo',
      '\t\techo "Installing: ${PACKAGE}";',
      '\t\tsudo /usr/bin/hdiutil attach ../l2tbinaries/macos/${PACKAGE}-*.dmg;',
      ('\t\tsudo /usr/sbin/installer -target / -pkg '
       '/Volumes/${PACKAGE}-*.pkg/${PACKAGE}-*.pkg;'),
      '\t\tsudo /usr/bin/hdiutil detach /Volumes/${PACKAGE}-*.pkg',
      '\tdone',
      '',
      'elif test ${TRAVIS_OS_NAME} = "linux";',
      'then',
      '\tsudo rm -f /etc/apt/sources.list.d/travis_ci_zeromq3-source.list;',
      '',
      '\tsudo add-apt-repository ppa:gift/dev -y;',
      '\tsudo apt-get update -q;',
      '',
      '\tif test ${TRAVIS_PYTHON_VERSION} = "2.7";',
      '\tthen',
      ('\t\tsudo apt-get install -y ${PYTHON2_DEPENDENCIES} '
       '${PYTHON2_TEST_DEPENDENCIES};'),
      '\telse',
      ('\t\tsudo apt-get install -y ${PYTHON3_DEPENDENCIES} '
       '${PYTHON3_TEST_DEPENDENCIES};'),
      '\tfi',
      '\tif test ${TARGET} = "pylint";',
      '\tthen',
      '\t\tsudo apt-get install -y pylint;',
      '\tfi',
      'fi',
      '']

  def Write(self):
    """Writes an install.sh file."""
    file_content = []
    file_content.extend(self._FILE_HEADER)

    dependencies = self._dependency_helper.GetL2TBinaries()
    dependencies = ' '.join(dependencies)
    file_content.append('L2TBINARIES_DEPENDENCIES="{0:s}";'.format(
        dependencies))

    file_content.append('')

    test_dependencies = ['funcsigs', 'mock', 'pbr']
    if 'six' not in dependencies:
      test_dependencies.append('six')

    if self._project_definition.name == 'artifacts':
      test_dependencies.append('yapf')

    test_dependencies = ' '.join(sorted(test_dependencies))
    file_content.append('L2TBINARIES_TEST_DEPENDENCIES="{0:s}";'.format(
        test_dependencies))

    file_content.append('')

    python2_dependencies = self._dependency_helper.GetDPKGDepends(
        exclude_version=True, python_version=2)
    python2_dependencies = ' '.join(python2_dependencies)
    file_content.append('PYTHON2_DEPENDENCIES="{0:s}";'.format(
        python2_dependencies))

    file_content.append('')

    test_dependencies = ['python-coverage', 'python-mock', 'python-tox']
    if self._project_definition.name == 'artifacts':
      # Note that the artifacts tests will use the Python 2 version of yapf.
      test_dependencies.append('python-yapf')
      test_dependencies.append('yapf')

    test_dependencies = ' '.join(sorted(test_dependencies))
    file_content.append('PYTHON2_TEST_DEPENDENCIES="{0:s}";'.format(
        test_dependencies))
    file_content.append('')

    python3_dependencies = self._dependency_helper.GetDPKGDepends(
        exclude_version=True, python_version=3)
    python3_dependencies = ' '.join(python3_dependencies)
    file_content.append('PYTHON3_DEPENDENCIES="{0:s}";'.format(
        python3_dependencies))

    file_content.append('')

    test_dependencies = ['python3-mock', 'python3-setuptools', 'python3-tox']
    if self._project_definition.name == 'artifacts':
      # Note that the artifacts tests will use the Python 2 version of yapf.
      test_dependencies.append('python-yapf')
      test_dependencies.append('yapf')

    test_dependencies = ' '.join(sorted(test_dependencies))
    file_content.append('PYTHON3_TEST_DEPENDENCIES="{0:s}";'.format(
        test_dependencies))

    file_content.extend(self._FILE_FOOTER)

    file_content = '\n'.join(file_content)
    file_content = file_content.encode('utf-8')

    with open(self.PATH, 'wb') as file_object:
      file_object.write(file_content)


class TravisRunWithTimeoutScriptWriter(DependencyFileWriter):
  """Travis-CI run_with_timeout.sh file writer."""

  _TEMPLATE_FILE = os.path.join('data', 'templates', 'run_with_timeout.sh')

  PATH = os.path.join('config', 'travis', 'run_with_timeout.sh')

  def Write(self):
    """Writes a _with_timeout.sh file."""
    template_mappings = {}

    template_file = os.path.join(self._l2tdevtools_path, self._TEMPLATE_FILE)
    file_content = self._GenerateFromTemplate(template_file, template_mappings)

    file_content = file_content.encode('utf-8')

    with open(self.PATH, 'wb') as file_object:
      file_object.write(file_content)


class TravisRunTestsScriptWriter(DependencyFileWriter):
  """Travis-CI runtests.sh file writer."""

  _TEMPLATE_FILE = os.path.join('data', 'templates', 'runtests.sh')

  PATH = os.path.join('config', 'travis', 'runtests.sh')

  def Write(self):
    """Writes a runtests.sh file."""
    paths_to_lint = [self._project_definition.name]
    for path_to_lint in ('config', 'scripts', 'tests', 'tools'):
      if os.path.isdir(path_to_lint):
        paths_to_lint.append(path_to_lint)

    paths_to_lint = sorted(paths_to_lint)
    if os.path.isfile('setup.py'):
      paths_to_lint.insert(0, 'setup.py')

    template_mappings = {
        'project_name': self._project_definition.name,
        'paths_to_lint': ' '.join(paths_to_lint)}

    template_file = os.path.join(self._l2tdevtools_path, self._TEMPLATE_FILE)
    file_content = self._GenerateFromTemplate(template_file, template_mappings)

    file_content = file_content.encode('utf-8')

    with open(self.PATH, 'wb') as file_object:
      file_object.write(file_content)


class TravisYmlWriter(DependencyFileWriter):
  """Travis.yml file writer."""

  _TEMPLATE_FILE = os.path.join('data', 'templates', '.travis.yml')

  PATH = '.travis.yml'

  def Write(self):
    """Writes a .travis.yml file."""
    template_mappings = {}

    template_file = os.path.join(self._l2tdevtools_path, self._TEMPLATE_FILE)
    file_content = self._GenerateFromTemplate(template_file, template_mappings)

    file_content = file_content.encode('utf-8')

    with open(self.PATH, 'wb') as file_object:
      file_object.write(file_content)


class ToxIniWriter(DependencyFileWriter):
  """Tox.ini file writer."""

  _TEMPLATE_FILE = os.path.join('data', 'templates', 'tox.ini')

  PATH = 'tox.ini'

  def Write(self):
    """Writes a tox.ini file."""
    test_dependencies = ['mock', 'pytest']
    if self._project_definition.name == 'artifacts':
      test_dependencies.append('yapf')

    test_dependencies = '\n'.join([
        '    {0:s}'.format(dependency) for dependency in test_dependencies])

    template_mappings = {
        'project_name': self._project_definition.name,
        'test_dependencies': test_dependencies}

    template_file = os.path.join(self._l2tdevtools_path, self._TEMPLATE_FILE)
    file_content = self._GenerateFromTemplate(template_file, template_mappings)

    file_content = file_content.encode('utf-8')

    with open(self.PATH, 'wb') as file_object:
      file_object.write(file_content)


if __name__ == '__main__':
  l2tdevtools_path = os.path.abspath(__file__)
  l2tdevtools_path = os.path.dirname(l2tdevtools_path)
  l2tdevtools_path = os.path.dirname(l2tdevtools_path)

  project_file = os.getcwd()
  project_file = os.path.basename(project_file)
  project_file = '{0:s}.ini'.format(project_file)

  project_reader = project_config.ProjectDefinitionReader()
  with open(project_file, 'rb') as file_object:
    project_definition = project_reader.Read(file_object)

  helper = dependencies.DependencyHelper()

  for writer_class in (
      AppveyorYmlWriter, PylintRcWriter, RequirementsWriter, SetupCfgWriter,
      TravisInstallScriptWriter, TravisRunWithTimeoutScriptWriter,
      TravisRunTestsScriptWriter, TravisYmlWriter, ToxIniWriter):
    writer = writer_class(l2tdevtools_path, project_definition, helper)
    writer.Write()

  for writer_class in (
      DependenciesPyWriter, DPKGControlWriter, GIFTCOPRInstallScriptWriter,
      GIFTPPAInstallScriptWriter):
    if not os.path.exists(writer_class.PATH):
      continue

    writer = writer_class(l2tdevtools_path, project_definition, helper)
    writer.Write()

  path = os.path.join(l2tdevtools_path, 'l2tdevtools', 'dependencies.py')
  file_data = []
  with open(path, 'rb') as file_object:
    for line in file_object.readlines():
      if 'GetDPKGDepends' in line:
        break

      file_data.append(line)

  file_data.pop()
  file_data = ''.join(file_data)

  path = os.path.join('utils', 'dependencies.py')
  with open(path, 'wb') as file_object:
    file_object.write(file_data)
