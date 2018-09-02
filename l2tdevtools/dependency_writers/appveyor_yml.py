# -*- coding: utf-8 -*-
"""Writer for appveyor.yml files."""

from __future__ import unicode_literals

import os

from l2tdevtools.dependency_writers import interface


class AppveyorYmlWriter(interface.DependencyFileWriter):
  """Appveyor.yml file writer."""

  PATH = os.path.join('appveyor.yml')

  _YEAR_SQLITE = '2018'
  _VERSION_SQLITE = '3230100'

  # yapf: disable

  _UPGRADE_PIP = (
      '- cmd: "%PYTHON%\\\\python.exe -m pip install --upgrade pip"')

  _INSTALL_PYWIN32_WMI = (
      '- cmd: "%PYTHON%\\\\python.exe -m pip install pywin32 WMI"')

  _POST_INSTALL_PYWIN32 = (
      '- cmd: "%PYTHON%\\\\python.exe %PYTHON%\\\\Scripts\\\\'
      'pywin32_postinstall.py -install"')

  _URL_L2TDEVTOOLS = 'https://github.com/log2timeline/l2tdevtools.git'

  _DOWNLOAD_L2TDEVTOOLS = (
      '- cmd: git clone {0:s} ..\\l2tdevtools'.format(_URL_L2TDEVTOOLS))

  _L2TDEVTOOLS = [
      _UPGRADE_PIP, _INSTALL_PYWIN32_WMI, _POST_INSTALL_PYWIN32,
      _DOWNLOAD_L2TDEVTOOLS]

  _FILE_HEADER = [
      'environment:',
      '  matrix:',
      '  - TARGET: python27',
      '    MACHINE_TYPE: "x86"',
      '    PYTHON: "C:\\\\Python27"',
      '  - TARGET: python27',
      '    MACHINE_TYPE: "amd64"',
      '    PYTHON: "C:\\\\Python27-x64"',
      '  - TARGET: python36',
      '    MACHINE_TYPE: "x86"',
      '    PYTHON: "C:\\\\Python36"',
      '  - TARGET: python36',
      '    MACHINE_TYPE: "amd64"',
      '    PYTHON: "C:\\\\Python36-x64"',
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
      '\'https://www.sqlite.org/{0:s}/sqlite-dll-win32-x86-{1:s}.zip\', '
      '\'C:\\Projects\\sqlite-dll-win32-x86-{1:s}.zip\')').format(
          _YEAR_SQLITE, _VERSION_SQLITE)

  _EXTRACT_SQLITE = (
      '- ps: $Output = Invoke-Expression -Command '
      '"& \'C:\\\\Program Files\\\\7-Zip\\\\7z.exe\' -y '
      '-oC:\\\\Projects\\\\ x C:\\\\Projects\\\\'
      'sqlite-dll-win32-x86-{0:s}.zip 2>&1"').format(_VERSION_SQLITE)

  _INSTALL_SQLITE = (
      '- cmd: copy C:\\Projects\\sqlite3.dll C:\\Python27\\DLLs\\')

  _SQLITE = [
      _SET_TLS_VERSION, _DOWNLOAD_SQLITE, _EXTRACT_SQLITE, _INSTALL_SQLITE
  ]

  _L2TDEVTOOLS_UPDATE = '\n'.join([
      '- cmd: if [%TARGET%]==[{0:s}] (',
      '    mkdir dependencies &&',
      '    set PYTHONPATH=..\\l2tdevtools &&',
      ('    "%PYTHON%\\\\python.exe" ..\\l2tdevtools\\tools\\update.py '
       '--download-directory dependencies --machine-type %MACHINE_TYPE% '
       '--msi-targetdir "%PYTHON%" --track dev {1:s} )')])

  _FILE_FOOTER = [
      '',
      'build: off',
      '',
      'test_script:',
      '- "%PYTHON%\\\\python.exe run_tests.py"',
      ''
  ]

  # yapf: enable

  def Write(self):
    """Writes an appveyor.yml file."""
    file_content = []
    file_content.extend(self._FILE_HEADER)

    if self._project_definition.name in ('l2tpreg', 'plaso'):
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
