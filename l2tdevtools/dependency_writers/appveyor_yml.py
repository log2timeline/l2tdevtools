# -*- coding: utf-8 -*-
"""Writer for appveyor.yml files."""

from __future__ import unicode_literals

import os

from l2tdevtools.dependency_writers import interface


class AppveyorYmlWriter(interface.DependencyFileWriter):
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
      '- cmd: git clone {0:s} ..\\l2tdevtools'.format(_URL_L2TDEVTOOLS))

  _L2TDEVTOOLS = [
      _UPGRADE_PIP, _INSTALL_PYWIN32_WMI, _POST_INSTALL_PYWIN32,
      _DOWNLOAD_L2TDEVTOOLS]

  _FILE_HEADER = [
      'environment:', '  matrix:', '  - TARGET: python27',
      '    PYTHON: "C:\\\\Python27"', '  - TARGET: python36',
      '    PYTHON: "C:\\\\Python36"', '']

  _ALLOW_FAILURES = ['matrix:', '  allow_failures:', '  - TARGET: python36', '']

  _INSTALL = [
      'install:', (
          '- cmd: \'"C:\\Program Files\\Microsoft SDKs\\Windows\\v7.1\\Bin\\'
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
      _SET_TLS_VERSION, _DOWNLOAD_SQLITE, _EXTRACT_SQLITE, _INSTALL_SQLITE
  ]

  _L2TDEVTOOLS_UPDATE = (
      '- cmd: mkdir dependencies && set PYTHONPATH=..\\l2tdevtools && '
      '"%PYTHON%\\\\python.exe" ..\\l2tdevtools\\tools\\update.py '
      '--download-directory dependencies --machine-type x86 '
      '--msi-targetdir "%PYTHON%" --track dev {0:s}')

  _FILE_FOOTER = [
      '', 'build: off', '', 'test_script:',
      '- "%PYTHON%\\\\python.exe run_tests.py"', ''
  ]

  def Write(self):
    """Writes an appveyor.yml file."""
    file_content = []
    file_content.extend(self._FILE_HEADER)

    if self._project_definition.name in ('dfvfs', 'l2tpreg', 'plaso'):
      file_content.extend(self._ALLOW_FAILURES)

    file_content.extend(self._INSTALL)

    dependencies = self._dependency_helper.GetL2TBinaries()
    dependencies.extend(['funcsigs', 'mock', 'pbr'])

    if 'six' not in dependencies:
      dependencies.append('six')

    if 'pysqlite' in dependencies:
      file_content.extend(self._SQLITE)

    if self._project_definition.name == 'artifacts':
      dependencies.append('yapf')

    if 'backports.lzma' in dependencies:
      dependencies.remove('backports.lzma')

    file_content.extend(self._L2TDEVTOOLS)

    dependencies = ' '.join(sorted(dependencies))
    l2tdevtools_update = self._L2TDEVTOOLS_UPDATE.format(dependencies)
    file_content.append(l2tdevtools_update)

    file_content.extend(self._FILE_FOOTER)

    file_content = '\n'.join(file_content)
    file_content = file_content.encode('utf-8')

    with open(self.PATH, 'wb') as file_object:
      file_object.write(file_content)
