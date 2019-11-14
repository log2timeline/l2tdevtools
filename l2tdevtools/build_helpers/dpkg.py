# -*- coding: utf-8 -*-
"""Helper for building projects from source."""

from __future__ import unicode_literals

import datetime
import glob
import logging
import os
import platform
import re
import shutil
import subprocess
import sys
import tarfile
import zipfile

from l2tdevtools import dpkg_files
from l2tdevtools import py2to3
from l2tdevtools.build_helpers import interface


class DPKGBuildHelper(interface.BuildHelper):
  """Helper to build dpkg packages (.deb).

  Attributes:
    architecture (str): dpkg target architecture.
    distribution (str): dpkg target distributions.
    version_suffix (str): dpkg version suffix.
  """

  _BUILD_DEPENDENCIES = frozenset([
      'git',
      'build-essential',
      'autotools-dev',
      'autoconf',
      'automake',
      'autopoint',
      'dh-autoreconf',
      'libtool',
      'gettext',
      'flex',
      'byacc',
      'debhelper',
      'devscripts',
      'dpkg-dev',
      'fakeroot',
      'quilt',
      'python-all',
      'python-all-dev',
      'python-setuptools',
  ])

  _BUILD_DEPENDENCY_PACKAGE_NAMES = {
      'bzip2': 'libbz2-dev',
      'fuse': 'libfuse-dev',
      'libcrypto': 'libssl-dev',
      'sqlite': 'libsqlite3-dev',
      'zeromq': 'libzmq3-dev',
      'zlib': 'zlib1g-dev'
  }

  def __init__(
      self, project_definition, l2tdevtools_path, dependency_definitions):
    """Initializes a build helper.

    Args:
      project_definition (ProjectDefinition): definition of the project
          to build.
      l2tdevtools_path (str): path to the l2tdevtools directory.
      dependency_definitions (dict[str, ProjectDefinition]): definitions of all
          projects, which is used to determine the properties of dependencies.
    """
    super(DPKGBuildHelper, self).__init__(
        project_definition, l2tdevtools_path, dependency_definitions)
    self._build_host_distribution = self._GetBuildHostDistribution()
    self._prep_script = 'prep-dpkg.sh'
    self._post_script = 'post-dpkg.sh'

    self.architecture = None
    self.distribution = None
    self.version_suffix = None

  def _BuildPrepare(
      self, source_directory, project_name, project_version, version_suffix,
      distribution, architecture):
    """Make the necessary preparations before building the dpkg packages.

    Args:
      source_directory (str): name of the source directory.
      project_name (str): name of the project.
      project_version (str): version of the project.
      version_suffix (str): version suffix.
      distribution (str): distribution.
      architecture (str): architecture.

    Returns:
      bool: True if the preparations were successful, False otherwise.
    """
    # Script to run before building, e.g. to change the dpkg packaging files.
    if os.path.exists(self._prep_script):
      command = 'sh ../{0:s} {1:s} {2!s} {3:s} {4:s} {5:s}'.format(
          self._prep_script, project_name, project_version, version_suffix,
          distribution, architecture)
      exit_code = subprocess.call('(cd {0:s} && {1:s})'.format(
          source_directory, command), shell=True)
      if exit_code != 0:
        logging.error('Running: "{0:s}" failed.'.format(command))
        return False

    return True

  def _BuildFinalize(
      self, source_directory, project_name, project_version, version_suffix,
      distribution, architecture):
    """Make the necessary finalizations after building the dpkg packages.

    Args:
      source_directory (str): name of the source directory.
      project_name (str): name of the project.
      project_version (str): version of the project.
      version_suffix (str): version suffix.
      distribution (str): distribution.
      architecture (str): architecture.

    Returns:
      bool: True if the finalizations were successful, False otherwise.
    """
    # Script to run after building, e.g. to automatically upload the dpkg
    # package files to an apt repository.
    if os.path.exists(self._post_script):
      command = 'sh ../{0:s} {1:s} {2!s} {3:s} {4:s} {5:s}'.format(
          self._post_script, project_name, project_version, version_suffix,
          distribution, architecture)
      exit_code = subprocess.call('(cd {0:s} && {1:s})'.format(
          source_directory, command), shell=True)
      if exit_code != 0:
        logging.error('Running: "{0:s}" failed.'.format(command))
        return False

    return True

  def _CheckIsInstalled(self, package_name):
    """Checks if a package is installed.

    Args:
      package_name (str): name of the package.

    Returns:
      bool: True if the package is installed, False otherwise.
    """
    command = 'dpkg-query -s {0:s} >/dev/null 2>&1'.format(package_name)
    exit_code = subprocess.call(command, shell=True)
    return exit_code == 0

  def _CreateOriginalSourcePackage(
      self, source_filename, project_name, project_version):
    """Creates the .orig.tar.gz source package.

    Args:
      source_filename (str): name of the source package file.
      project_name (str): project name.
      project_version (str): version of the project.
    """
    if self._project_definition.dpkg_source_name:
      project_name = self._project_definition.dpkg_source_name

    deb_orig_source_filename = '{0:s}_{1!s}.orig.tar.gz'.format(
        project_name, project_version)
    if os.path.exists(deb_orig_source_filename):
      return

    if source_filename.endswith('.zip'):
      self._CreateOriginalSourcePackageFromZip(
          source_filename, deb_orig_source_filename)
    else:
      # TODO: add fix psutil package name.
      shutil.copy(source_filename, deb_orig_source_filename)

  def _CreateOriginalSourcePackageFromZip(
      self, source_filename, orig_source_filename):
    """Creates the .orig.tar.gz source package from a .zip file.

    Args:
      source_filename (str): name of the source package file.
      orig_source_filename (str): name of the .orig.tar.gz source package file.
    """
    with zipfile.ZipFile(source_filename, 'r') as zip_file:
      with tarfile.open(name=orig_source_filename, mode='w:gz') as tar_file:
        for filename in zip_file.namelist():
          with zip_file.open(filename) as file_object:
            zip_info = zip_file.getinfo(filename)
            tar_info = tarfile.TarInfo(filename)
            tar_info.size = zip_info.file_size
            # Populate modification times from zip file into tar archive,
            # as launchpad refuses to build packages containing files with
            # timestamps too far in the past.
            date_time = zip_info.date_time
            mtime = datetime.datetime(*date_time)
            mtime = int((mtime - datetime.datetime(1970, 1, 1)).total_seconds())
            tar_info.mtime = mtime
            tar_file.addfile(tar_info, fileobj=file_object)

  def _CreatePackagingFiles(self, source_directory, project_version):
    """Creates packaging files.

    Args:
      source_directory (str): name of the source directory.
      project_version (str): project version.

    Returns:
      bool: True if successful, False otherwise.
    """
    debian_directory = os.path.join(source_directory, 'debian')

    # If there is a debian directory remove it and recreate it from
    # the dpkg directory.
    if os.path.exists(debian_directory):
      logging.info('Removing: {0:s}'.format(debian_directory))
      shutil.rmtree(debian_directory)

    dpkg_directory = os.path.join(source_directory, 'dpkg')

    if not os.path.exists(dpkg_directory):
      dpkg_directory = os.path.join(source_directory, 'config', 'dpkg')

    if os.path.exists(dpkg_directory):
      shutil.copytree(dpkg_directory, debian_directory)

    else:
      build_configuration = self._DetermineBuildConfiguration(source_directory)  # pylint: disable=assignment-from-none

      os.chdir(source_directory)

      try:
        build_files_generator = dpkg_files.DPKGBuildFilesGenerator(
            self._project_definition, project_version, self._data_path,
            self._dependency_definitions,
            build_configuration=build_configuration)

        build_files_generator.GenerateFiles('debian')

      finally:
        os.chdir('..')

    if not os.path.exists(debian_directory):
      logging.error('Missing debian sub directory in: {0:s}'.format(
          source_directory))
      return False

    return True

  # pylint: disable=redundant-returns-doc,unused-argument
  def _DetermineBuildConfiguration(self, source_directory):
    """Determines the build configuration of a project.

    Args:
      source_directory (str): path of the source directory.

    Returns:
      DPKGBuildConfiguration: dpkg build configuration or None if the build
          configuration could not be determined.
    """
    return None

  def _GetBuildHostDistribution(self):
    """Determines the Debian/Ubuntu distribution name of the build host.

    This information can be found in the configuration file "/etc/lsb-release"
    if preset. Otherwise this information can be obtained by invoking
    "/usr/bin/lsb_release -sc".

    Returns:
      str: Debian/Ubuntu distribution name or None if the value could not
          be determined.
    """
    distribution_name = None

    lsb_release_path = '/etc/lsb-release'
    if os.path.exists(lsb_release_path):
      lsb_release = self._ReadLSBReleaseConfigurationFile(lsb_release_path)
      distribution_name = lsb_release.get('distrib_codename', None)

    if not distribution_name:
      output = self._RunLSBReleaseCommand(option='-sc')
      if output:
        distribution_name = output.strip() or None

    return distribution_name

  def _ReadLSBReleaseConfigurationFile(self, path):
    """Reads a lsb-release configuration (/etc/lsb-release) file.

    This function ignores comment lines, lines that are not UTF-8 formatted
    and lines that do not consist of "key=value".

    Args:
      path (str): path of the lsb-release configuration file.

    Returns:
      dict[str, str]: key value pairs that are stored in the lsb-release
          configuration file.
    """
    lsb_release_values = {}
    with open(path, 'rb') as file_object:
      for line in file_object.readlines():
        try:
          line = line.decode('utf-8').strip()
        except UnicodeDecodeError:
          continue

        if not line.startswith('#') and '=' in line:
          line = line.lower()
          key, _, value = line.partition('=')
          lsb_release_values[key.strip()] = value.strip() or None

    return lsb_release_values

  def _RemoveOlderDPKGPackages(self, project_name, project_version):
    """Removes previous versions of dpkg packages.

    Args:
      project_name (str): project name.
      project_version (str): project version.
    """
    filenames_to_ignore = '^{0:s}[-_].*{1!s}'.format(
        project_name, project_version)
    filenames_to_ignore = re.compile(filenames_to_ignore)

    # Remove files of previous versions in the format:
    # project[-_]*version-[1-9]_architecture.*
    filenames_glob = '{0:s}[-_]*-[1-9]_{1:s}.*'.format(
        project_name, self.architecture)
    filenames = glob.glob(filenames_glob)

    for filename in filenames:
      if not filenames_to_ignore.match(filename):
        logging.info('Removing: {0:s}'.format(filename))
        os.remove(filename)

    # Remove files of previous versions in the format:
    # project[-_]*version-[1-9].*
    filenames_glob = '{0:s}[-_]*-[1-9].*'.format(project_name)
    filenames = glob.glob(filenames_glob)

    for filename in filenames:
      if not filenames_to_ignore.match(filename):
        logging.info('Removing: {0:s}'.format(filename))
        os.remove(filename)

  def _RemoveOlderOriginalSourcePackage(
      self, project_name, project_version, version_suffix=None,
      distribution=None):
    """Removes previous versions of original source package.

    Args:
      project_name (str): name of the project.
      project_version (str): version of the project.
      version_suffix (str): version suffix.
      distribution (str): distribution.
    """
    filenames_to_ignore = '^{0:s}_{1!s}.orig.tar.gz'.format(
        project_name, project_version)

    filenames_to_ignore = re.compile(filenames_to_ignore)

    # Remove files of previous versions in the format:
    # project_version.orig.tar.gz
    if version_suffix and distribution:
      filenames_glob = '{0:s}_*{1:s}~{2:s}.orig.tar.gz'.format(
          project_name, version_suffix, distribution)
    else:
      filenames_glob = '{0:s}_*.orig.tar.gz'.format(project_name)

    filenames = glob.glob(filenames_glob)

    for filename in filenames:
      if not filenames_to_ignore.match(filename):
        logging.info('Removing: {0:s}'.format(filename))
        os.remove(filename)

  def _RemoveOlderSourceDPKGPackages(self, project_name, project_version):
    """Removes previous versions of source dpkg packages.

    Args:
      project_name (str): project name.
      project_version (str): project version.
    """
    filenames_to_ignore = '^{0:s}[-_].*{1!s}'.format(
        project_name, project_version)
    filenames_to_ignore = re.compile(filenames_to_ignore)

    # Remove files of previous versions in the format:
    # project[-_]version-[1-9]suffix~distribution_architecture.*
    filenames_glob = '{0:s}[-_]*-[1-9]{1:s}~{2:s}_{3:s}.*'.format(
        project_name, self.version_suffix, self.distribution, self.architecture)
    filenames = glob.glob(filenames_glob)

    for filename in filenames:
      if not filenames_to_ignore.match(filename):
        logging.info('Removing: {0:s}'.format(filename))
        os.remove(filename)

    # Remove files of previous versions in the format:
    # project[-_]*version-[1-9]suffix~distribution.*
    filenames_glob = '{0:s}[-_]*-[1-9]{1:s}~{2:s}.*'.format(
        project_name, self.version_suffix, self.distribution)
    filenames = glob.glob(filenames_glob)

    for filename in filenames:
      if not filenames_to_ignore.match(filename):
        logging.info('Removing: {0:s}'.format(filename))
        os.remove(filename)

  def _RunLSBReleaseCommand(self, option='-a'):
    """Runs the lsb-release command (/usr/bin/lsb_release).

    Args:
      option (Optional[str]): option to pass to the lsb-release command.

    Returns:
      str: output of the command or None if there is no lsb-release command
          available, or running the command failed, or the output cannot be
          decoded.
    """
    output = None
    path = '/usr/bin/lsb_release'

    if os.path.exists(path):
      process = subprocess.Popen(
          [path, option], stderr=subprocess.PIPE, stdout=subprocess.PIPE)

      output, _ = process.communicate()
      if not process or process.returncode != 0:
        output = None

      elif isinstance(output, py2to3.BYTES_TYPE):
        try:
          output = output.decode('utf-8')
        except UnicodeDecodeError:
          output = None

    return output

  def CheckBuildDependencies(self):
    """Checks if the build dependencies are met.

    Returns:
      list[str]: build dependency names that are not met or an empty list.
    """
    missing_packages = []
    for package_name in self._BUILD_DEPENDENCIES:
      if not self._CheckIsInstalled(package_name):
        missing_packages.append(package_name)

      if not self._IsPython2Only() and 'python' in package_name:
        package_name = package_name.replace('python', 'python3')
        if not self._CheckIsInstalled(package_name):
          missing_packages.append(package_name)

    for name in self._project_definition.build_dependencies:
      package_name = self._BUILD_DEPENDENCY_PACKAGE_NAMES.get(name, name)
      if package_name not in self._project_definition.dpkg_build_dependencies:
        self._project_definition.dpkg_build_dependencies.append(package_name)

    for package_name in self._project_definition.dpkg_build_dependencies:
      if not self._CheckIsInstalled(package_name):
        missing_packages.append(package_name)

      if not self._IsPython2Only() and 'python' in package_name:
        package_name = package_name.replace('python', 'python3')
        if not self._CheckIsInstalled(package_name):
          missing_packages.append(package_name)

    return missing_packages

  def CheckProjectConfiguration(self):
    """Checks if the project configuration is correct.

    This functions checks if all build dependencies are defined as dpkg build
    dependencies.

    Returns:
      bool: True if the project configuration is correct, False otherwise.
    """
    result = True
    for name in self._project_definition.build_dependencies:
      package_name = self._BUILD_DEPENDENCY_PACKAGE_NAMES.get(name, name)
      if package_name not in self._project_definition.dpkg_build_dependencies:
        logging.warning((
            'Build dependency: {0:s} not defined as dpkg build '
            'dependency: {1:s}.').format(name, package_name))
        result = False

    return result


class ConfigureMakeDPKGBuildHelper(DPKGBuildHelper):
  """Helper to build dpkg packages (.deb)."""

  def __init__(
      self, project_definition, l2tdevtools_path, dependency_definitions):
    """Initializes a build helper.

    Args:
      project_definition (ProjectDefinition): definition of the project
          to build.
      l2tdevtools_path (str): path to the l2tdevtools directory.
      dependency_definitions (dict[str, ProjectDefinition]): definitions of all
          projects, which is used to determine the properties of dependencies.
    """
    super(ConfigureMakeDPKGBuildHelper, self).__init__(
        project_definition, l2tdevtools_path, dependency_definitions)
    self.architecture = platform.machine()
    self.distribution = ''
    self.version_suffix = ''

    if self.architecture == 'i686':
      self.architecture = 'i386'
    elif self.architecture == 'x86_64':
      self.architecture = 'amd64'

  def Build(self, source_helper_object):
    """Builds the dpkg packages.

    Args:
      source_helper_object (SourceHelper): source helper.

    Returns:
      bool: True if successful, False otherwise.
    """
    source_filename = source_helper_object.GetSourcePackageFilename()
    if not source_filename:
      logging.info('Missing source package of: {0:s}'.format(
          source_helper_object.project_name))
      return False

    source_directory = source_helper_object.GetSourceDirectoryPath()
    if not source_directory:
      logging.info('Missing source directory of: {0:s}'.format(
          source_helper_object.project_name))
      return False

    project_version = source_helper_object.GetProjectVersion()

    # dpkg-buildpackage wants an source package filename without
    # the status indication and orig indication.
    self._CreateOriginalSourcePackage(
        source_filename, source_helper_object.project_name, project_version)

    logging.info('Building deb of: {0:s}'.format(source_filename))

    if not self._CreatePackagingFiles(source_directory, project_version):
      return False

    # If there is a temporary packaging directory remove it.
    temporary_directory = os.path.join(source_directory, 'tmp')
    if os.path.exists(temporary_directory):
      logging.info('Removing: {0:s}'.format(temporary_directory))
      shutil.rmtree(temporary_directory)

    if not self._BuildPrepare(
        source_directory, source_helper_object.project_name, project_version,
        self.version_suffix, self.distribution, self.architecture):
      return False

    log_file_path = os.path.join('..', self.LOG_FILENAME)
    command = 'dpkg-buildpackage -uc -us -rfakeroot > {0:s} 2>&1'.format(
        log_file_path)
    exit_code = subprocess.call('(cd {0:s} && {1:s})'.format(
        source_directory, command), shell=True)
    if exit_code != 0:
      logging.error('Running: "{0:s}" failed.'.format(command))
      return False

    if not self._BuildFinalize(
        source_directory, source_helper_object.project_name, project_version,
        self.version_suffix, self.distribution, self.architecture):
      return False

    return True

  def CheckBuildRequired(self, source_helper_object):
    """Checks if a build is required.

    Args:
      source_helper_object (SourceHelper): source helper.

    Returns:
      bool: True if a build is required, False otherwise.
    """
    project_version = source_helper_object.GetProjectVersion()

    deb_filename = '{0:s}_{1!s}-1_{2:s}.deb'.format(
        source_helper_object.project_name, project_version, self.architecture)

    return not os.path.exists(deb_filename)

  def Clean(self, source_helper_object):
    """Cleans the dpkg packages in the current directory.

    Args:
      source_helper_object (SourceHelper): source helper.
    """
    project_version = source_helper_object.GetProjectVersion()

    self._RemoveOlderOriginalSourcePackage(
        source_helper_object.project_name, project_version)

    self._RemoveOlderDPKGPackages(
        source_helper_object.project_name, project_version)


class ConfigureMakeSourceDPKGBuildHelper(DPKGBuildHelper):
  """Helper to build source dpkg packages (.deb)."""

  def __init__(
      self, project_definition, l2tdevtools_path, dependency_definitions):
    """Initializes a build helper.

    Args:
      project_definition (ProjectDefinition): definition of the project
          to build.
      l2tdevtools_path (str): path to the l2tdevtools directory.
      dependency_definitions (dict[str, ProjectDefinition]): definitions of all
          projects, which is used to determine the properties of dependencies.
    """
    super(ConfigureMakeSourceDPKGBuildHelper, self).__init__(
        project_definition, l2tdevtools_path, dependency_definitions)
    self._prep_script = 'prep-dpkg-source.sh'
    self._post_script = 'post-dpkg-source.sh'
    self.architecture = 'source'
    self.distribution = 'bionic'
    self.version_suffix = 'ppa1'

  def Build(self, source_helper_object):
    """Builds the dpkg packages.

    Args:
      source_helper_object (SourceHelper): source helper.

    Returns:
      bool: True if successful, False otherwise.
    """
    source_filename = source_helper_object.GetSourcePackageFilename()
    if not source_filename:
      logging.info('Missing source package of: {0:s}'.format(
          source_helper_object.project_name))
      return False

    source_directory = source_helper_object.GetSourceDirectoryPath()
    if not source_directory:
      logging.info('Missing source directory of: {0:s}'.format(
          source_helper_object.project_name))
      return False

    project_version = source_helper_object.GetProjectVersion()

    self._CreateOriginalSourcePackage(
        source_filename, source_helper_object.project_name, project_version)

    logging.info('Building source deb of: {0:s}'.format(source_filename))

    if not self._CreatePackagingFiles(source_directory, project_version):
      return False

    # If there is a temporary packaging directory remove it.
    temporary_directory = os.path.join(source_directory, 'tmp')
    if os.path.exists(temporary_directory):
      logging.info('Removing: {0:s}'.format(temporary_directory))
      shutil.rmtree(temporary_directory)

    if not self._BuildPrepare(
        source_directory, source_helper_object.project_name, project_version,
        self.version_suffix, self.distribution, self.architecture):
      return False

    log_file_path = os.path.join('..', self.LOG_FILENAME)
    command = 'debuild -S -sa > {0:s} 2>&1'.format(log_file_path)
    exit_code = subprocess.call('(cd {0:s} && {1:s})'.format(
        source_directory, command), shell=True)
    if exit_code != 0:
      logging.error(
          'Failed to run: "(cd {0:s} && {1:s})" with exit code {2:d}.'.format(
              source_directory, command, exit_code))
      return False

    if not self._BuildFinalize(
        source_directory, source_helper_object.project_name, project_version,
        self.version_suffix, self.distribution, self.architecture):
      return False

    return True

  def CheckBuildRequired(self, source_helper_object):
    """Checks if a build is required.

    Args:
      source_helper_object (SourceHelper): source helper.

    Returns:
      bool: True if a build is required, False otherwise.
    """
    project_version = source_helper_object.GetProjectVersion()

    changes_filename = '{0:s}_{1!s}-1{2:s}~{3:s}_{4:s}.changes'.format(
        source_helper_object.project_name, project_version,
        self.version_suffix, self.distribution, self.architecture)

    return not os.path.exists(changes_filename)

  def Clean(self, source_helper_object):
    """Cleans the source dpkg packages in the current directory.

    Args:
      source_helper_object (SourceHelper): source helper.
    """
    project_version = source_helper_object.GetProjectVersion()

    self._RemoveOlderOriginalSourcePackage(
        source_helper_object.project_name, project_version)

    self._RemoveOlderSourceDPKGPackages(
        source_helper_object.project_name, project_version)


class SetupPyDPKGBuildHelperBase(DPKGBuildHelper):
  """Shared functionality for setup.py build system dpkg build helpers."""

  def _DetermineBuildConfiguration(self, source_directory):
    """Determines the build configuration of a project that has setup.py.

    Args:
      source_directory (str): path of the source directory.

    Returns:
      DPKGBuildConfiguration: dpkg build configuration or None if the build
          configuration could not be determined.
    """
    installroot_path = os.path.join(source_directory, 'installroot')

    command = (
        '{0:s} setup.py install --root=installroot --prefix=/usr> /dev/null '
        '2>&1').format(sys.executable)
    exit_code = subprocess.call('(cd {0:s} && {1:s})'.format(
        source_directory, command), shell=True)
    if exit_code != 0:
      logging.error('Running: "{0:s}" failed.'.format(command))
      build_configuration = None

    else:
      build_configuration = dpkg_files.DPKGBuildConfiguration()

      if os.path.exists(os.path.join(installroot_path, 'usr', 'bin')):
        build_configuration.has_bin_directory = True

      dist_packages = os.path.join(
          # While it should be expected the modules are moved in dist-packages,
          # since we're building debian packages, adding --prefix flag disables
          # this in setuptools. See
          # https://bugs.launchpad.net/ubuntu/+source/python2.6/+bug/362570
          # https://lists.ubuntu.com/archives/ubuntu-devel/2009-February/027439.html
          installroot_path, 'usr', 'lib', 'python2.7', 'site-packages')

      for directory_entry in os.listdir(dist_packages):
        directory_entry_path = os.path.join(dist_packages, directory_entry)

        if directory_entry.endswith('.egg-info'):
          # pylint: disable=simplifiable-if-statement
          if os.path.isdir(directory_entry_path):
            build_configuration.has_egg_info_directory = True
          else:
            build_configuration.has_egg_info_file = True

        elif os.path.isdir(directory_entry_path):
          if directory_entry != '__pycache__':
            build_configuration.module_directories.append(directory_entry)

            # TODO: determine depth of module directories.

        elif directory_entry.endswith('.py'):
          build_configuration.has_module_source_files = True

        elif directory_entry.endswith('.so'):
          build_configuration.has_module_shared_object = True

    if os.path.exists(installroot_path):
      shutil.rmtree(installroot_path)

    return build_configuration


class SetupPyDPKGBuildHelper(SetupPyDPKGBuildHelperBase):
  """Helper to build dpkg packages (.deb) using setup.py build system."""

  def __init__(
      self, project_definition, l2tdevtools_path, dependency_definitions):
    """Initializes a build helper.

    Args:
      project_definition (ProjectDefinition): definition of the project
          to build.
      l2tdevtools_path (str): path to the l2tdevtools directory.
      dependency_definitions (dict[str, ProjectDefinition]): definitions of all
          projects, which is used to determine the properties of dependencies.
    """
    super(SetupPyDPKGBuildHelper, self).__init__(
        project_definition, l2tdevtools_path, dependency_definitions)
    self.architecture = platform.machine()
    self.distribution = ''
    self.version_suffix = ''

    if not project_definition.architecture_dependent:
      self.architecture = 'all'
    elif self.architecture == 'i686':
      self.architecture = 'i386'
    elif self.architecture == 'x86_64':
      self.architecture = 'amd64'

  def _GetFilenameSafeProjectInformation(self, source_helper_object):
    """Determines the filename safe project name and version.

    Args:
      source_helper_object (SourceHelper): source helper.

    Returns:
      tuple: contains:

        * str: filename safe project name.
        * str: version.
    """
    if self._project_definition.dpkg_name:
      project_name = self._project_definition.dpkg_name
    else:
      project_name = source_helper_object.project_name
      if not project_name.startswith('python-'):
        project_name = 'python-{0:s}'.format(project_name)

    project_version = source_helper_object.GetProjectVersion()
    if project_version and project_version.startswith('1!'):
      # Remove setuptools epoch.
      project_version = project_version[2:]

    return project_name, project_version

  def Build(self, source_helper_object):
    """Builds the dpkg packages.

    Args:
      source_helper_object (SourceHelper): source helper.

    Returns:
      bool: True if successful, False otherwise.
    """
    source_filename = source_helper_object.GetSourcePackageFilename()
    if not source_filename:
      logging.info('Missing source package of: {0:s}'.format(
          source_helper_object.project_name))
      return False

    source_directory = source_helper_object.GetSourceDirectoryPath()
    if not source_directory:
      logging.info('Missing source directory of: {0:s}'.format(
          source_helper_object.project_name))
      return False

    project_name, project_version = self._GetFilenameSafeProjectInformation(
        source_helper_object)

    # dpkg-buildpackage wants an source package filename without
    # the status indication and orig indication.
    self._CreateOriginalSourcePackage(
        source_filename, source_helper_object.project_name, project_version)

    logging.info('Building deb of: {0:s}'.format(source_filename))

    if not self._CreatePackagingFiles(source_directory, project_version):
      return False

    # If there is a temporary packaging directory remove it.
    temporary_directory = os.path.join(source_directory, 'tmp')
    if os.path.exists(temporary_directory):
      logging.info('Removing: {0:s}'.format(temporary_directory))
      shutil.rmtree(temporary_directory)

    if not self._BuildPrepare(
        source_directory, project_name, project_version, self.version_suffix,
        self.distribution, self.architecture):
      return False

    log_file_path = os.path.join('..', self.LOG_FILENAME)
    command = 'dpkg-buildpackage -uc -us -rfakeroot > {0:s} 2>&1'.format(
        log_file_path)
    exit_code = subprocess.call('(cd {0:s} && {1:s})'.format(
        source_directory, command), shell=True)
    if exit_code != 0:
      logging.error(
          'Failed to run: "(cd {0:s} && {1:s})" with exit code {2:d}.'.format(
              source_directory, command, exit_code))
      return False

    if not self._BuildFinalize(
        source_directory, project_name, project_version, self.version_suffix,
        self.distribution, self.architecture):
      return False

    return True

  def CheckBuildRequired(self, source_helper_object):
    """Checks if a build is required.

    Args:
      source_helper_object (SourceHelper): source helper.

    Returns:
      bool: True if a build is required, False otherwise.
    """
    project_name, project_version = self._GetFilenameSafeProjectInformation(
        source_helper_object)

    deb_filename = '{0:s}_{1!s}-1_{2:s}.deb'.format(
        project_name, project_version, self.architecture)

    return not os.path.exists(deb_filename)

  def Clean(self, source_helper_object):
    """Cleans the dpkg packages in the current directory.

    Args:
      source_helper_object (SourceHelper): source helper.
    """
    project_name, project_version = self._GetFilenameSafeProjectInformation(
        source_helper_object)

    self._RemoveOlderOriginalSourcePackage(
        source_helper_object.project_name, project_version)

    self._RemoveOlderDPKGPackages(project_name, project_version)

    if not self._IsPython2Only() and project_name.startswith('python-'):
      project_name = 'python3-{0:s}'.format(project_name[7])

      self._RemoveOlderDPKGPackages(project_name, project_version)


class SetupPySourceDPKGBuildHelper(SetupPyDPKGBuildHelperBase):
  """Helper to build source dpkg packages using setup.py build system."""

  def __init__(
      self, project_definition, l2tdevtools_path, dependency_definitions):
    """Initializes a build helper.

    Args:
      project_definition (ProjectDefinition): definition of the project
          to build.
      l2tdevtools_path (str): path to the l2tdevtools directory.
      dependency_definitions (dict[str, ProjectDefinition]): definitions of all
          projects, which is used to determine the properties of dependencies.
    """
    super(SetupPySourceDPKGBuildHelper, self).__init__(
        project_definition, l2tdevtools_path, dependency_definitions)
    self._prep_script = 'prep-dpkg-source.sh'
    self._post_script = 'post-dpkg-source.sh'
    self.architecture = 'source'
    self.distribution = 'bionic'
    self.version_suffix = 'ppa1'

  def _GetFilenameSafeProjectInformation(self, source_helper_object):
    """Determines the filename safe project name and version.

    Args:
      source_helper_object (SourceHelper): source helper.

    Returns:
      tuple: contains:

        * str: filename safe project name.
        * str: version.
    """
    if self._project_definition.dpkg_source_name:
      project_name = self._project_definition.dpkg_source_name
    else:
      project_name = source_helper_object.project_name
      if not project_name.startswith('python-'):
        project_name = 'python-{0:s}'.format(project_name)

    project_version = source_helper_object.GetProjectVersion()
    if project_version and project_version.startswith('1!'):
      # Remove setuptools epoch.
      project_version = project_version[2:]

    return project_name, project_version

  def Build(self, source_helper_object):
    """Builds the dpkg packages.

    Args:
      source_helper_object (SourceHelper): source helper.

    Returns:
      bool: True if successful, False otherwise.
    """
    source_filename = source_helper_object.GetSourcePackageFilename()
    if not source_filename:
      logging.info('Missing source package of: {0:s}'.format(
          source_helper_object.project_name))
      return False

    source_directory = source_helper_object.GetSourceDirectoryPath()
    if not source_directory:
      logging.info('Missing source directory of: {0:s}'.format(
          source_helper_object.project_name))
      return False

    project_name, project_version = self._GetFilenameSafeProjectInformation(
        source_helper_object)

    self._CreateOriginalSourcePackage(
        source_filename, source_helper_object.project_name, project_version)

    logging.info('Building source deb of: {0:s}'.format(source_filename))

    if not self._CreatePackagingFiles(source_directory, project_version):
      return False

    # If there is a temporary packaging directory remove it.
    temporary_directory = os.path.join(source_directory, 'tmp')
    if os.path.exists(temporary_directory):
      logging.info('Removing: {0:s}'.format(temporary_directory))
      shutil.rmtree(temporary_directory)

    if not self._BuildPrepare(
        source_directory, project_name, project_version, self.version_suffix,
        self.distribution, self.architecture):
      return False

    log_file_path = os.path.join('..', self.LOG_FILENAME)
    command = 'debuild -S -sa > {0:s} 2>&1'.format(log_file_path)
    exit_code = subprocess.call('(cd {0:s} && {1:s})'.format(
        source_directory, command), shell=True)
    if exit_code != 0:
      logging.error(
          'Failed to run: "(cd {0:s} && {1:s})" with exit code {2:d}.'.format(
              source_directory, command, exit_code))

    if not self._BuildFinalize(
        source_directory, project_name, project_version, self.version_suffix,
        self.distribution, self.architecture):
      return False

    return True

  def CheckBuildRequired(self, source_helper_object):
    """Checks if a build is required.

    Args:
      source_helper_object (SourceHelper): source helper.

    Returns:
      bool: True if a build is required, False otherwise.
    """
    project_name, project_version = self._GetFilenameSafeProjectInformation(
        source_helper_object)

    changes_filename = '{0:s}_{1!s}-1{2:s}~{3:s}_{4:s}.changes'.format(
        project_name, project_version, self.version_suffix, self.distribution,
        self.architecture)

    return not os.path.exists(changes_filename)

  def Clean(self, source_helper_object):
    """Cleans the dpkg packages in the current directory.

    Args:
      source_helper_object (SourceHelper): source helper.
    """
    project_version = source_helper_object.GetProjectVersion()

    self._RemoveOlderOriginalSourcePackage(
        source_helper_object.project_name, project_version,
        version_suffix=self.version_suffix, distribution=self.distribution)

    self._RemoveOlderSourceDPKGPackages(
        source_helper_object.project_name, project_version)
