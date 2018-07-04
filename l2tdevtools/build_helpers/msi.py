# -*- coding: utf-8 -*-
"""Helper for building projects from source."""

from __future__ import print_function
from __future__ import unicode_literals

import fileinput
import glob
import logging
import os
import platform
import re
import shutil
import subprocess
import sys

from l2tdevtools import source_helper
from l2tdevtools.build_helpers import interface
from l2tdevtools.download_helpers import zlib


class MSIBuildHelper(interface.BuildHelper):
  """Helper to build Microsoft Installer packages (.msi)."""

  _COMMON_PATCH_EXE_PATHS = [
      '{0:s}:{1:s}{2:s}'.format(
          'C', os.sep, os.path.join('GnuWin', 'bin', 'patch.exe')),
      '{0:s}:{1:s}{2:s}'.format(
          'C', os.sep, os.path.join('GnuWin32', 'bin', 'patch.exe')),
      '{0:s}:{1:s}{2:s}'.format(
          'C', os.sep, os.path.join(
              'Program Files (x86)', 'GnuWin', 'bin', 'patch.exe')),
      '{0:s}:{1:s}{2:s}'.format(
          'C', os.sep, os.path.join(
              'Program Files (x86)', 'GnuWin32', 'bin', 'patch.exe')),
      '{0:s}:{1:s}{2:s}'.format(
          'C', os.sep, os.path.join(
              'ProgramData', 'chocolatey', 'bin', 'patch.exe'))
  ]

  def __init__(self, project_definition, l2tdevtools_path):
    """Initializes a build helper.

    Args:
      project_definition (ProjectDefinition): project definition.
      l2tdevtools_path (str): path to the l2tdevtools directory.
    """
    super(MSIBuildHelper, self).__init__(project_definition, l2tdevtools_path)
    self._python_version_suffix = 'py{0:d}.{1:d}'.format(
        sys.version_info[0], sys.version_info[1])
    self.architecture = platform.machine()

    if self.architecture == 'x86':
      self.architecture = 'win32'
    elif self.architecture == 'AMD64':
      self.architecture = 'win-amd64'

  def _ApplyPatches(self, patches):
    """Applies patches.

    Args:
      source_directory (str): name of the source directory.
      patches (list[str]): patch file names.

    Returns:
      bool: True if applying the patches was successful.
    """
    # Search common locations for patch.exe
    patch_exe_path = None
    for patch_exe_path in self._COMMON_PATCH_EXE_PATHS:
      if os.path.exists(patch_exe_path):
        break

    if not patch_exe_path:
      logging.error('Unable to find patch.exe')
      return False

    for patch_filename in patches:
      filename = os.path.join(self._data_path, 'patches', patch_filename)
      if not os.path.exists(filename):
        logging.warning('Missing patch file: {0:s}'.format(filename))
        continue

      command = '\"{0:s}\" --force --binary --input {1:s}'.format(
          patch_exe_path, filename)
      exit_code = subprocess.call(command, shell=False)
      if exit_code != 0:
        logging.error('Running: "{0:s}" failed.'.format(command))
        return False

    return True

  def _RunPreBuildScript(self, script):
    """Runs the msi_prebuild script.

    Args:
      script (str): the script's filename.

    Returns:
      bool: True if running the script was successful.
    """
    filepath = os.path.join(self._data_path, 'msi_prebuild', script)
    if filepath.endswith('.ps1'):
      command = 'Powershell.exe -ExecutionPolicy ByPass "{0:s}"'.format(
          filepath)

    elif filepath.endswith('py'):
      command = '{0:s} "{1:s}"'.format(sys.executable, filepath)

    exit_code = subprocess.call(command, shell=False)
    if exit_code != 0:
      logging.error('Running: "{0:s}" failed.'.format(command))
      return False

    return True


class ConfigureMakeMSIBuildHelper(MSIBuildHelper):
  """Helper to build Microsoft Installer packages (.msi)."""

  def __init__(self, project_definition, l2tdevtools_path):
    """Initializes a build helper.

    Args:
      project_definition (ProjectDefinition): project definition.
      l2tdevtools_path (str): path to the l2tdevtools directory.

    Raises:
      RuntimeError: if the Visual Studio version could not be determined.
    """
    super(ConfigureMakeMSIBuildHelper, self).__init__(
        project_definition, l2tdevtools_path)

    if 'VS150COMNTOOLS' in os.environ:
      self.version = '2017'

    elif 'VS140COMNTOOLS' in os.environ:
      self.version = '2015'

    elif 'VS120COMNTOOLS' in os.environ:
      self.version = '2013'

    elif 'VS110COMNTOOLS' in os.environ:
      self.version = '2012'

    elif 'VS100COMNTOOLS' in os.environ:
      self.version = '2010'

    # Since the script exports VS90COMNTOOLS to the environment we need
    # to check the other Visual Studio environment variables first.
    elif 'VS90COMNTOOLS' in os.environ:
      self.version = '2008'

    elif 'VCINSTALLDIR' in os.environ:
      self.version = 'python'

    else:
      raise RuntimeError('Unable to determine Visual Studio version.')

  def _BuildMSBuild(self, source_helper_object, source_directory):
    """Builds using Visual Studio and MSBuild.

    Args:
      source_helper_object (SourceHelper): source helper.
      source_directory (str): name of the source directory.

    Returns:
      bool: True if successful, False otherwise.
    """
    # Search common locations for MSBuild.exe
    if self.version == '2008':
      msbuild = '{0:s}:{1:s}{2:s}'.format(
          'C', os.sep, os.path.join(
              'Windows', 'Microsoft.NET', 'Framework', 'v3.5',
              'MSBuild.exe'))

    # Note that MSBuild in .NET 3.5 does not support vs2010 solution files
    # and MSBuild in .NET 4.0 is needed instead.
    elif self.version in ('2010', '2012', '2013', '2015', '2017'):
      msbuild = '{0:s}:{1:s}{2:s}'.format(
          'C', os.sep, os.path.join(
              'Windows', 'Microsoft.NET', 'Framework', 'v4.0.30319',
              'MSBuild.exe'))

    else:
      msbuild = ''

    if not msbuild or not os.path.exists(msbuild):
      logging.error('Unable to find MSBuild.exe')
      return False

    if self.version == '2008':
      if not os.environ['VS90COMNTOOLS']:
        logging.error('Missing VS90COMNTOOLS environment variable.')
        return False

    elif self.version == '2010':
      if not os.environ['VS100COMNTOOLS']:
        logging.error('Missing VS100COMNTOOLS environment variable.')
        return False

    elif self.version == '2012':
      if not os.environ['VS110COMNTOOLS']:
        logging.error('Missing VS110COMNTOOLS environment variable.')
        return False

    elif self.version == '2013':
      if not os.environ['VS120COMNTOOLS']:
        logging.error('Missing VS120COMNTOOLS environment variable.')
        return False

    elif self.version == '2015':
      if not os.environ['VS140COMNTOOLS']:
        logging.error('Missing VS140COMNTOOLS environment variable.')
        return False

    elif self.version == '2017':
      if not os.environ['VS150COMNTOOLS']:
        logging.error('Missing VS150COMNTOOLS environment variable.')
        return False

    elif self.version == 'python':
      if not os.environ['VCINSTALLDIR']:
        logging.error('Missing VCINSTALLDIR environment variable.')
        return False

    zlib_project_file = os.path.join(
        source_directory, 'msvscpp', 'zlib', 'zlib.vcproj')
    zlib_source_directory = os.path.join(
        os.path.dirname(source_directory), 'zlib')

    if (os.path.exists(zlib_project_file) and
        not os.path.exists(zlib_source_directory)):
      logging.error('Missing dependency: zlib.')
      return False

    dokan_project_file = os.path.join(
        source_directory, 'msvscpp', 'dokan', 'dokan.vcproj')
    dokan_source_directory = os.path.join(
        os.path.dirname(source_directory), 'dokan')

    if (os.path.exists(dokan_project_file) and
        not os.path.exists(dokan_source_directory)):
      logging.error('Missing dependency: dokan.')
      return False

    # Detect architecture based on Visual Studion Platform environment
    self._BuildPrepare(source_helper_object, source_directory)

    # variable. If not set the platform with default to Win32.
    msvscpp_platform = os.environ.get('Platform', None)
    if not msvscpp_platform:
      msvscpp_platform = os.environ.get('TARGET_CPU', None)

    if not msvscpp_platform or msvscpp_platform == 'x86':
      msvscpp_platform = 'Win32'

    if msvscpp_platform not in ('Win32', 'x64'):
      logging.error('Unsupported build platform: {0:s}'.format(
          msvscpp_platform))
      return False

    if self.version == '2008' and msvscpp_platform == 'x64':
      logging.error('Unsupported 64-build platform for vs2008.')
      return False

    filenames_glob = os.path.join(source_directory, 'msvscpp', '*.sln')
    solution_filenames = glob.glob(filenames_glob)

    if len(solution_filenames) != 1:
      logging.error('Unable to find Visual Studio solution file')
      return False

    solution_filename = solution_filenames[0]

    command = (
        '\"{0:s}\" /p:Configuration=Release /p:Platform={1:s} '
        '/noconsolelogger /fileLogger /maxcpucount {2:s}').format(
            msbuild, msvscpp_platform, solution_filename)
    exit_code = subprocess.call(command, shell=False)
    if exit_code != 0:
      logging.error('Running: "{0:s}" failed.'.format(command))
      return False

    python_module_name, _, _ = source_directory.partition('-')
    python_module_name = 'py{0:s}'.format(python_module_name[3:])
    python_module_directory = os.path.join(
        source_directory, python_module_name)
    python_module_dist_directory = os.path.join(
        python_module_directory, 'dist')

    if os.path.exists(python_module_dist_directory):
      return True

    build_directory = os.path.join('..', '..')

    os.chdir(python_module_directory)

    result = self._BuildSetupPy()
    if result:
      result = self._MoveMSI(python_module_name, build_directory)

    os.chdir(build_directory)

    return result

  def _BuildPrepare(self, source_helper_object, source_directory):
    """Prepares the source for building with Visual Studio.

    Args:
      source_helper_object (SourceHelper): source helper.
      source_directory (str): name of the source directory.
    """
    # For the vs2008 build make sure the binary is XP compatible,
    # by setting WINVER to 0x0501. For the vs2010 build WINVER is
    # set to 0x0600 (Windows Vista).

    # WINVER is set in common\config_winapi.h or common\config_msc.h.
    config_filename = os.path.join(
        source_directory, 'common', 'config_winapi.h')

    # If the WINAPI configuration file is not available use
    # the MSC compiler configuration file instead.
    if not os.path.exists(config_filename):
      config_filename = os.path.join(
          source_directory, 'common', 'config_msc.h')

    # Add a line to the config file that sets WINVER.
    parsing_mode = 0

    for line in fileinput.input(config_filename, inplace=1):
      # Remove trailing whitespace and end-of-line characters.
      line = line.rstrip()

      if parsing_mode != 2 or line:
        if parsing_mode == 1:
          # TODO: currently we want libbde not use Windows Crypto API, hence
          # we set WINVER to 0x0501.
          if (self.version == '2008' or
              source_helper_object.project_name == 'libbde'):
            if not line.startswith(b'#define WINVER 0x0501'):
              print(b'#define WINVER 0x0501')
              print(b'')

          else:
            if not line.startswith(b'#define WINVER 0x0600'):
              print(b'#define WINVER 0x0600')
              print(b'')

          parsing_mode = 2

        elif line.startswith(b'#define _CONFIG_'):
          parsing_mode = 1

      print(line)

  def _BuildSetupPy(self):
    """Builds using Visual Studio and setup.py.

    This function assumes setup.py is present in the current working
    directory.

    Returns:
      bool: True if successful, False otherwise.
    """
    # Setup.py uses VS90COMNTOOLS which is vs2008 specific
    # so we need to set it for the other Visual Studio versions.
    if self.version == '2010':
      os.environ['VS90COMNTOOLS'] = os.environ['VS100COMNTOOLS']

    elif self.version == '2012':
      os.environ['VS90COMNTOOLS'] = os.environ['VS110COMNTOOLS']

    elif self.version == '2013':
      os.environ['VS90COMNTOOLS'] = os.environ['VS120COMNTOOLS']

    elif self.version == '2015':
      os.environ['VS90COMNTOOLS'] = os.environ['VS140COMNTOOLS']

    elif self.version == '2017':
      os.environ['VS90COMNTOOLS'] = os.environ['VS150COMNTOOLS']

    elif self.version == 'python':
      os.environ['VS90COMNTOOLS'] = os.environ['VCINSTALLDIR']

    command = '\"{0:s}\" setup.py bdist_msi'.format(sys.executable)
    exit_code = subprocess.call(command, shell=False)
    if exit_code != 0:
      logging.error('Running: "{0:s}" failed.'.format(command))
      return False

    return True

  def _MoveMSI(self, python_module_name, build_directory):
    """Moves the MSI from the dist sub directory into the build directory.

    Args:
      python_module_name (str): Python module name.
      build_directory (str): build directory.

    Returns:
      bool: True if the move was successful, False otherwise.
    """
    filenames_glob = os.path.join(
        'dist', '{0:s}-*.msi'.format(python_module_name))
    filenames = glob.glob(filenames_glob)

    if len(filenames) != 1:
      logging.error('Unable to find MSI file: {0:s}.'.format(filenames_glob))
      return False

    _, _, msi_filename = filenames[0].rpartition(os.path.sep)
    msi_filename = os.path.join(build_directory, msi_filename)
    if os.path.exists(msi_filename):
      logging.warning('MSI file already exists.')
    else:
      logging.info('Moving: {0:s}'.format(filenames[0]))
      shutil.move(filenames[0], build_directory)

    return True

  def _SetupBuildDependencyDokan(self):
    """Sets up the dokan build dependency.

    Returns:
      bool: True if successful, False otherwise.
    """
    # TODO: implement.
    return False

  def _SetupBuildDependencyZeroMQ(self):
    """Sets up the zeromq build dependency.

    Returns:
      bool: True if successful, False otherwise.
    """
    # TODO: implement.
    return False

  def _SetupBuildDependencyZlib(self):
    """Sets up the zlib build dependency.

    Returns:
      bool: True if successful, False otherwise.
    """
    download_helper = zlib.ZlibDownloadHelper('http://www.zlib.net')
    source_helper_object = source_helper.SourcePackageHelper(
        'zlib', None, download_helper)

    source_filename = source_helper_object.Download()
    if not source_filename:
      logging.info('Download of: {0:s} failed'.format(
          source_helper_object.project_name))
      return False

    source_directory = source_helper_object.Create()
    if not source_directory:
      logging.error(
          'Extraction of source package: {0:s} failed'.format(
              source_filename))
      return False

    if not os.path.exists('zlib'):
      os.rename(source_directory, 'zlib')

    return True

  def CheckBuildDependencies(self):
    """Checks if the build dependencies are met.

    Returns:
      list[str]: build dependency names that are not met or an empty list.
    """
    missing_packages = []
    for package_name in self._project_definition.build_dependencies:
      if package_name == 'fuse':
        self._SetupBuildDependencyDokan()

      elif package_name == 'zeromq':
        self._SetupBuildDependencyZeroMQ()

      elif package_name == 'zlib':
        self._SetupBuildDependencyZlib()

      elif package_name != 'libcrypto':
        missing_packages.append(package_name)

    return missing_packages

  def Build(self, source_helper_object):
    """Builds using Visual Studio.

    Args:
      source_helper_object (SourceHelper): source helper.

    Returns:
      bool: True if successful, False otherwise.
    """
    source_filename = source_helper_object.Download()
    if not source_filename:
      logging.info('Download of: {0:s} failed'.format(
          source_helper_object.project_name))
      return False

    source_directory = source_helper_object.Create()
    if not source_directory:
      logging.error(
          'Extraction of source package: {0:s} failed'.format(source_filename))
      return False

    logging.info('Building: {0:s} with Visual Studio {1:s}'.format(
        source_filename, self.version))

    if self._project_definition.patches:
      os.chdir(source_directory)
      result = self._ApplyPatches(self._project_definition.patches)
      os.chdir('..')

      if not result:
        return False

    result = False

    setup_py_path = os.path.join(source_directory, 'setup.py')
    if not os.path.exists(setup_py_path):
      result = self._BuildMSBuild(source_helper_object, source_directory)

    else:
      python_module_name, _, _ = source_directory.partition('-')
      project_version = source_helper_object.GetProjectVersion()

      msi_filename = '{0:s}-python-{1!s}.1.{2:s}-{3:s}.msi'.format(
          python_module_name, project_version, self.architecture,
          self._python_version_suffix)
      msi_path = os.path.join(source_directory, 'dist', msi_filename)

      if os.path.exists(msi_path):
        logging.warning('MSI file already exists.')
        result = True
      else:
        build_directory = os.path.join('..')

        os.chdir(source_directory)

        result = self._BuildSetupPy()
        if result:
          result = self._MoveMSI(python_module_name, build_directory)

        os.chdir(build_directory)

    return result

  def CheckBuildRequired(self, source_helper_object):
    """Checks if a build is required.

    Args:
      source_helper_object (SourceHelper): source helper.

    Returns:
      bool: True if a build is required, False otherwise.
    """
    project_version = source_helper_object.GetProjectVersion()

    msi_filename = '{0:s}-python-{1!s}.1.{2:s}-{3:s}.msi'.format(
        source_helper_object.project_name, project_version, self.architecture,
        self._python_version_suffix)

    return not os.path.exists(msi_filename)

  def Clean(self, source_helper_object):
    """Cleans the build and dist directory.

    Args:
      source_helper_object (SourceHelper): source helper.
    """
    project_version = source_helper_object.GetProjectVersion()

    # Remove previous versions of MSIs.
    filenames_to_ignore = 'py{0:s}-.*{1!s}.1.{2:s}-{3:s}'.format(
        source_helper_object.project_name[3:], project_version,
        self.architecture, self._python_version_suffix)
    filenames_to_ignore = re.compile(filenames_to_ignore)

    filenames_glob = 'py{0:s}-*.1.{1:s}-{2:s}.msi'.format(
        source_helper_object.project_name[3:], self.architecture,
        self._python_version_suffix)
    filenames = glob.glob(filenames_glob)

    for filename in filenames:
      if not filenames_to_ignore.match(filename):
        logging.info('Removing: {0:s}'.format(filename))
        os.remove(filename)

    filenames_to_ignore = '{0:s}-python-.*{1!s}.1.{2:s}-{3:s}.msi'.format(
        source_helper_object.project_name, project_version, self.architecture,
        self._python_version_suffix)
    filenames_to_ignore = re.compile(filenames_to_ignore)

    filenames_glob = '{0:s}-python-*.1.{1:s}-{2:s}.msi'.format(
        source_helper_object.project_name, self.architecture,
        self._python_version_suffix)
    filenames = glob.glob(filenames_glob)

    for filename in filenames:
      if not filenames_to_ignore.match(filename):
        logging.info('Removing: {0:s}'.format(filename))
        os.remove(filename)


class SetupPyMSIBuildHelper(MSIBuildHelper):
  """Helper to build Microsoft Installer packages (.msi)."""

  def _GetFilenameSafeProjectInformation(self, source_helper_object):
    """Determines the filename safe project name and version.

    Args:
      source_helper_object (SourceHelper): source helper.

    Returns:
      tuple: contains:

        * str: filename safe project name.
        * str: version.
    """
    if self._project_definition.setup_name:
      project_name = self._project_definition.setup_name
    else:
      project_name = source_helper_object.project_name

    project_version = source_helper_object.GetProjectVersion()

    if source_helper_object.project_name == 'dfvfs':
      project_version = '{0!s}.1'.format(project_version)
    else:
      project_version = '{0!s}'.format(project_version)

    return project_name, project_version

  def Build(self, source_helper_object):
    """Builds the msi.

    Args:
      source_helper_object (SourceHelper): source helper.

    Returns:
      bool: True if successful, False otherwise.
    """
    source_filename = source_helper_object.Download()
    if not source_filename:
      logging.info('Download of: {0:s} failed'.format(
          source_helper_object.project_name))
      return False

    source_directory = source_helper_object.Create()
    if not source_directory:
      logging.error(
          'Extraction of source package: {0:s} failed'.format(source_filename))
      return False

    logging.info('Building msi of: {0:s}'.format(source_filename))

    if self._project_definition.patches:
      os.chdir(source_directory)
      result = self._ApplyPatches(self._project_definition.patches)
      os.chdir('..')

      if not result:
        return False

    if self._project_definition.msi_prebuild:
      os.chdir(source_directory)
      result = self._RunPreBuildScript(self._project_definition.msi_prebuild)
      os.chdir('..')

      if not result:
        return False

    if (sys.version_info[0] >= 3 and
        source_helper_object.project_name == 'pycrypto'):
      # Work-around for compilation issue with Visual Studio 2017. Also see:
      # https://stackoverflow.com/questions/41843266/microsoft-windows-python-3-6-pycrypto-installation-error
      include_path = os.path.join(
          os.environ['VCINSTALLDIR'], 'Tools', 'MSVC', '14.14.26428',
          'include', 'stdint.h')
      os.environ['CL'] = '-FI"{0:s}"'.format(include_path)

    log_file_path = os.path.join('..', self.LOG_FILENAME)
    command = '\"{0:s}\" setup.py bdist_msi > {1:s} 2>&1'.format(
        sys.executable, log_file_path)
    exit_code = subprocess.call('(cd {0:s} && {1:s})'.format(
        source_directory, command), shell=True)
    if exit_code != 0:
      logging.error('Running: "{0:s}" failed.'.format(command))
      return False

    # Move the msi to the build directory.
    project_name, _ = self._GetFilenameSafeProjectInformation(
        source_helper_object)

    filenames_glob = os.path.join(
        source_directory, 'dist', '{0:s}-*.msi'.format(project_name))
    filenames = glob.glob(filenames_glob)

    if len(filenames) != 1:
      logging.error('Unable to find MSI file: {0:s}.'.format(filenames_glob))
      return False

    _, _, msi_filename = filenames[0].rpartition(os.path.sep)
    if os.path.exists(msi_filename):
      logging.warning('MSI file already exists.')
    else:
      logging.info('Moving: {0:s}'.format(filenames[0]))
      shutil.move(filenames[0], '.')

    return True

  def CheckBuildDependencies(self):
    """Checks if the build dependencies are met.

    Returns:
      list[str]: build dependency names that are not met or an empty list.
    """
    missing_packages = []
    for package_name in self._project_definition.build_dependencies:
      # Ignore sqlite dependency for MSI builds
      if package_name != 'sqlite':
        missing_packages.append(package_name)
    return missing_packages

  def CheckBuildRequired(self, source_helper_object):
    """Checks if a build is required.

    Args:
      source_helper_object (SourceHelper): source helper.

    Returns:
      bool: True if a build is required, False otherwise.
    """
    project_name, project_version = self._GetFilenameSafeProjectInformation(
        source_helper_object)

    # TODO: it looks like coverage is no architecture dependent on Windows.
    # Check if it is architecture dependent on other platforms.
    if (self._project_definition.architecture_dependent and
        project_name != 'coverage'):
      suffix = '-{0:s}'.format(self._python_version_suffix)
    else:
      suffix = ''

    # MSI does not support a single number version therefore we add '.1'.
    if '.' not in project_version:
      project_version = '{0!s}.1'.format(project_version)

    # MSI does not support a 4 digit version, e.g. '1.2.3.4' therefore
    # we remove the last digit.
    elif len(project_version.split('.')) == 4:
      project_version, _, _ = project_version.rpartition('.')

    # MSI does not support a version containing a '-', e.g. '1.2.3-4'
    # therefore we remove the digit after the '-'.
    elif '-' in project_version:
      project_version, _, _ = project_version.rpartition('-')

    msi_filename = '{0:s}-{1:s}.{2:s}{3:s}.msi'.format(
        project_name, project_version, self.architecture, suffix)

    return not os.path.exists(msi_filename)

  def Clean(self, source_helper_object):
    """Cleans the build and dist directory.

    Args:
      source_helper_object (SourceHelper): source helper.
    """
    # Remove previous versions build directories.
    for filename in ('build', 'dist'):
      if os.path.exists(filename):
        logging.info('Removing: {0:s}'.format(filename))
        shutil.rmtree(filename, True)

    # Remove previous versions of MSIs.
    project_name, project_version = self._GetFilenameSafeProjectInformation(
        source_helper_object)

    if self._project_definition.architecture_dependent:
      suffix = '-{0:s}'.format(self._python_version_suffix)
    else:
      suffix = ''

    # MSI does not support a single number version therefore we add '.1'.
    if '.' not in project_version:
      project_version = '{0!s}.1'.format(project_version)

    # MSI does not support a 4 digit version, e.g. '1.2.3.4' there we remove
    # the last digit.
    elif len(project_version.split('.')) == 4:
      project_version, _, _ = project_version.rpartition('.')

    # MSI does not support a version containing a '-', e.g. '1.2.3-4' there
    # we remove the digit after the '-'.
    elif '-' in project_version:
      project_version, _, _ = project_version.rpartition('-')

    filenames_to_ignore = '{0:s}-.*{1!s}.{2:s}{3:s}.msi'.format(
        project_name, project_version, self.architecture, suffix)
    filenames_to_ignore = re.compile(filenames_to_ignore)

    filenames_glob = '{0:s}-*.{1:s}{2:s}.msi'.format(
        project_name, self.architecture, suffix)
    filenames = glob.glob(filenames_glob)

    for filename in filenames:
      if not filenames_to_ignore.match(filename):
        logging.info('Removing: {0:s}'.format(filename))
        os.remove(filename)
