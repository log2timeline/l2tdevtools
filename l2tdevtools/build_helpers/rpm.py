# -*- coding: utf-8 -*-
"""Helper for building projects from source."""

from __future__ import unicode_literals

import glob
import logging
import os
import platform
import re
import shutil
import subprocess

from l2tdevtools.build_helpers import interface
from l2tdevtools import py2to3
from l2tdevtools import spec_file


class BaseRPMBuildHelper(interface.BuildHelper):
  """Helper to build RPM packages (.rpm)."""

  _BUILD_DEPENDENCIES = frozenset([
      'git',
      'binutils',
      'autoconf',
      'automake',
      'libtool',
      'gettext-devel',
      'make',
      'pkgconf',
      'gcc',
      'gcc-c++',
      'flex',
      'byacc',
      'rpm-build',
      'python2-dateutil',
      'python2-devel',
      'python2-setuptools',
      'python2-test',
      'python3-dateutil',
      'python3-devel',
      'python3-setuptools',
      'python3-test',
  ])

  _BUILD_DEPENDENCY_PACKAGE_NAMES = {
      'bzip2': ['bzip2-devel'],
      'fuse': ['fuse-devel'],
      'libcrypto': ['openssl-devel'],
      'pytest-runner': [
          'python2-pytest-runner', 'python3-pytest-runner'],
      'sqlite': ['sqlite-devel'],
      'zeromq': ['libzmq3-devel'],
      'zlib': ['zlib-devel']
  }

  def __init__(self, project_definition, l2tdevtools_path):
    """Initializes a build helper.

    Args:
      project_definition (ProjectDefinition): project definition.
      l2tdevtools_path (str): path to the l2tdevtools directory.
    """
    super(BaseRPMBuildHelper, self).__init__(
        project_definition, l2tdevtools_path)
    self.architecture = platform.machine()

    self.rpmbuild_path = os.path.join('~', 'rpmbuild')
    self.rpmbuild_path = os.path.expanduser(self.rpmbuild_path)

    self._rpmbuild_rpms_path = os.path.join(self.rpmbuild_path, 'RPMS')
    self._rpmbuild_sources_path = os.path.join(self.rpmbuild_path, 'SOURCES')
    self._rpmbuild_specs_path = os.path.join(self.rpmbuild_path, 'SPECS')
    self._rpmbuild_srpms_path = os.path.join(self.rpmbuild_path, 'SRPMS')

  def _BuildFromSpecFile(self, spec_filename, rpmbuild_flags='-ba'):
    """Builds the rpms directly from a spec file.

    Args:
      spec_filename (str): name of the spec file as stored in the rpmbuild
          SPECS sub directory.
      rpmbuild_flags (Optional(str)): rpmbuild flags.

    Returns:
      bool: True if successful, False otherwise.
    """
    spec_filename = os.path.join('SPECS', spec_filename)

    current_path = os.getcwd()
    os.chdir(self.rpmbuild_path)

    command = 'rpmbuild {0:s} {1:s} > {2:s} 2>&1'.format(
        rpmbuild_flags, spec_filename, self.LOG_FILENAME)
    exit_code = subprocess.call(command, shell=True)
    if exit_code != 0:
      logging.error('Running: "{0:s}" failed.'.format(command))

    os.chdir(current_path)

    return exit_code == 0

  def _BuildFromSourcePackage(
      self, source_package_filename, rpmbuild_flags='-ta'):
    """Builds the rpms directly from the source package file.

    For this to work the source package needs to contain a valid rpm .spec file.

    Args:
      source_package_filename (str): name of the source package file.
      rpmbuild_flags (Optional(str)): rpmbuild flags.

    Returns:
      bool: True if successful, False otherwise.
    """
    command = 'rpmbuild {0:s} {1:s} > {2:s} 2>&1'.format(
        rpmbuild_flags, source_package_filename, self.LOG_FILENAME)
    exit_code = subprocess.call(command, shell=True)
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
    command = 'rpm -qi {0:s} >/dev/null 2>&1'.format(package_name)
    exit_code = subprocess.call(command, shell=True)
    return exit_code == 0

  def _CopySourcePackageToRPMBuildSources(self, source_package_filename):
    """Copies the source package to the rpmbuild SOURCES directory.

    Args:
      source_package_filename (str): name of the source package file.
    """
    rpm_source_package_path = os.path.join(
        self._rpmbuild_sources_path, source_package_filename)

    if not os.path.exists(rpm_source_package_path):
      self._CreateRPMbuildDirectories()

      shutil.copy(source_package_filename, rpm_source_package_path)

  def _CreateRPMbuildDirectories(self):
    """Creates the rpmbuild and sub directories."""
    if not os.path.exists(self.rpmbuild_path):
      os.mkdir(self.rpmbuild_path)

    if not os.path.exists(self._rpmbuild_sources_path):
      os.mkdir(self._rpmbuild_sources_path)

    if not os.path.exists(self._rpmbuild_specs_path):
      os.mkdir(self._rpmbuild_specs_path)

  def _CreateSpecFile(self, project_name, spec_file_data):
    """Creates a spec file in the rpmbuild directory.

    Args:
      project_name (str): name of the project.
      spec_file_data (str): spec file data.
    """
    spec_filename = os.path.join(
        self._rpmbuild_specs_path, '{0:s}.spec'.format(project_name))

    rpm_spec_file = open(spec_filename, 'w')
    rpm_spec_file.write(spec_file_data)
    rpm_spec_file.close()

  def _CopySourceFile(self, source_package_filename):
    """Copies the source file to the rpmbuild directory.

    Args:
      source_package_filename (str): name of the source package file.
    """
    shutil.copy(source_package_filename, self._rpmbuild_sources_path)

  def _GetFilenameSafeProjectInformation(self, source_helper_object):
    """Determines the filename safe project name and version.

    Args:
      source_helper_object (SourceHelper): source helper.

    Returns:
      tuple: contains:

        * str: filename safe project name.
        * str: version.
    """
    project_name = source_helper_object.project_name
    if (self._project_definition.setup_name and
        project_name not in ('bencode', 'dateutil')):
      project_name = self._project_definition.setup_name

    project_version = source_helper_object.GetProjectVersion()
    if project_version and project_version.startswith('1!'):
      # Remove setuptools epoch.
      project_version = project_version[2:]

    if isinstance(project_version, py2to3.STRING_TYPES):
      project_version = project_version.replace('-', '_')

    return project_name, project_version

  def _GetSetupPySpecFilePath(self, source_helper_object, source_directory):
    """Retrieves the path of the setup.py generated .spec file.

    Args:
      source_helper_object (SourceHelper): source helper.
      source_directory (str): name of the source directory.

    Returns:
      str: path of the setup.py generated .spec file.
    """
    if self._project_definition.setup_name:
      setup_name = self._project_definition.setup_name
    else:
      setup_name = source_helper_object.project_name

    spec_filename = '{0:s}.spec'.format(setup_name)

    return os.path.join(source_directory, 'dist', spec_filename)

  def _MoveFilesToCurrentDirectory(self, filenames_glob):
    """Moves files into the current directory.

    Args:
      filenames_glob (str): glob of the filenames to move.
    """
    filenames = glob.glob(filenames_glob)
    for filename in filenames:
      logging.info('Moving: {0:s}'.format(filename))

      local_filename = os.path.basename(filename)
      if os.path.exists(local_filename):
        os.remove(local_filename)

      shutil.move(filename, '.')

  def CheckBuildDependencies(self):
    """Checks if the build dependencies are met.

    Returns:
      list[str]: build dependency names that are not met or an empty list.
    """
    missing_packages = []
    for package_name in self._BUILD_DEPENDENCIES:
      if not self._CheckIsInstalled(package_name):
        missing_packages.append(package_name)

    for package_name in self._project_definition.build_dependencies:
      dependencies = self._BUILD_DEPENDENCY_PACKAGE_NAMES.get(
          package_name, package_name)
      for dependency in dependencies:
        if not self._CheckIsInstalled(dependency):
          missing_packages.append(dependency)

    return missing_packages


class RPMBuildHelper(BaseRPMBuildHelper):
  """Helper to build RPM packages (.rpm)."""

  def _RemoveBuildDirectory(self, project_name, project_version):
    """Removes build directory.

    Args:
      project_name (str): name of the project.
      project_version (str): version of the project.
    """
    filename = '{0:s}-{1!s}'.format(project_name, project_version)
    filename = os.path.join(self.rpmbuild_path, 'BUILD', filename)

    logging.info('Removing: {0:s}'.format(filename))

    try:
      shutil.rmtree(filename)
    except OSError:
      logging.warning('Unable to remove: {0:s}'.format(filename))

  def _RemoveOlderBuildDirectory(self, project_name, project_version):
    """Removes previous versions of build directories.

    Args:
      project_name (str): name of the project.
      project_version (str): version of the project.
    """
    filenames_to_ignore = '{0:s}-{1!s}'.format(
        project_name, project_version)
    filenames_to_ignore = re.compile(filenames_to_ignore)

    filenames_glob = os.path.join(
        self.rpmbuild_path, 'BUILD', '{0:s}-*'.format(project_name))
    filenames = glob.glob(filenames_glob)

    for filename in filenames:
      if not filenames_to_ignore.match(filename):
        logging.info('Removing: {0:s}'.format(filename))
        shutil.rmtree(filename)

  def _RemoveOlderRPMs(self, project_name, project_version):
    """Removes previous versions of .rpm files.

    Args:
      project_name (str): name of the project.
      project_version (str): version of the project.
    """
    filenames_to_ignore = '{0:s}-.*{1!s}-1.{2:s}.rpm'.format(
        project_name, project_version, self.architecture)
    filenames_to_ignore = re.compile(filenames_to_ignore)

    rpm_filenames_glob = '{0:s}-*-1.{1:s}.rpm'.format(
        project_name, self.architecture)
    filenames = glob.glob(rpm_filenames_glob)

    for filename in filenames:
      if not filenames_to_ignore.match(filename):
        logging.info('Removing: {0:s}'.format(filename))
        os.remove(filename)

    filenames_glob = os.path.join(
        self.rpmbuild_path, 'RPMS', self.architecture, rpm_filenames_glob)
    filenames = glob.glob(filenames_glob)

    for filename in filenames:
      if not filenames_to_ignore.match(filename):
        logging.info('Removing: {0:s}'.format(filename))
        os.remove(filename)

  def CheckBuildRequired(self, source_helper_object):
    """Checks if a build is required.

    Args:
      source_helper_object (SourceHelper): source helper.

    Returns:
      bool: True if a build is required, False otherwise.
    """
    project_name, project_version = self._GetFilenameSafeProjectInformation(
        source_helper_object)

    rpm_filename = '{0:s}-{1!s}-1.{2:s}.rpm'.format(
        project_name, project_version, self.architecture)

    return not os.path.exists(rpm_filename)


class ConfigureMakeRPMBuildHelper(RPMBuildHelper):
  """Helper to build RPM packages (.rpm)."""

  def _MoveRPMs(self, project_name, project_version):
    """Moves the rpms from the rpmbuild directory into the current directory.

    Args:
      project_name (str): name of the project.
      project_version (str): version of the project.
    """
    filenames_glob = '{0:s}-*{1!s}-1.{2:s}.rpm'.format(
        project_name, project_version, self.architecture)
    filenames_glob = os.path.join(
        self._rpmbuild_rpms_path, self.architecture, filenames_glob)

    self._MoveFilesToCurrentDirectory(filenames_glob)

  def Build(self, source_helper_object):
    """Builds the rpms.

    Args:
      source_helper_object (SourceHelper): source helper.

    Returns:
      bool: True if successful, False otherwise.
    """
    source_package_filename = source_helper_object.Download()
    if not source_package_filename:
      logging.info('Download of: {0:s} failed'.format(
          source_helper_object.project_name))
      return False

    logging.info('Building rpm of: {0:s}'.format(source_package_filename))

    project_name, project_version = self._GetFilenameSafeProjectInformation(
        source_helper_object)

    # rpmbuild wants the source package filename without the status indication.
    rpm_source_package_filename = '{0:s}-{1!s}.tar.gz'.format(
        project_name, project_version)
    os.rename(source_package_filename, rpm_source_package_filename)

    build_successful = self._BuildFromSourcePackage(
        rpm_source_package_filename, rpmbuild_flags='-tb')

    if build_successful:
      self._MoveRPMs(project_name, project_version)
      self._RemoveBuildDirectory(project_name, project_version)

    # Change the source package filename back to the original.
    os.rename(rpm_source_package_filename, source_package_filename)

    return build_successful

  def Clean(self, source_helper_object):
    """Cleans the rpmbuild directory.

    Args:
      source_helper_object (SourceHelper): source helper.
    """
    project_name, project_version = self._GetFilenameSafeProjectInformation(
        source_helper_object)

    self._RemoveOlderBuildDirectory(project_name, project_version)
    self._RemoveOlderRPMs(project_name, project_version)


class SetupPyRPMBuildHelper(RPMBuildHelper):
  """Helper to build RPM packages (.rpm)."""

  def __init__(self, project_definition, l2tdevtools_path):
    """Initializes a build helper.

    Args:
      project_definition (ProjectDefinition): project definition.
      l2tdevtools_path (str): path to the l2tdevtools directory.
    """
    super(SetupPyRPMBuildHelper, self).__init__(
        project_definition, l2tdevtools_path)
    if not project_definition.architecture_dependent:
      self.architecture = 'noarch'

  def _GenerateSpecFile(
      self, project_name, project_version, source_filename,
      source_helper_object):
    """Generates the rpm spec file.

    Args:
      project_name (str): name of the project.
      project_version (str): version of the project.
      source_filename (str): name of the source package file.
      source_helper_object (SourceHelper): source helper.

    Returns:
      str: path of the generated rpm spec file or None.
    """
    source_directory = source_helper_object.Create()
    if not source_directory:
      logging.error(
          'Extraction of source package: {0:s} failed'.format(source_filename))
      return

    spec_file_generator = spec_file.RPMSpecFileGenerator(self._data_path)

    log_file_path = os.path.join('..', self.LOG_FILENAME)
    if not spec_file_generator.GenerateWithSetupPy(
        source_directory, log_file_path):
      return

    if project_name.startswith('python-'):
      project_name = project_name[7:]

    input_file_path = self._GetSetupPySpecFilePath(
        source_helper_object, source_directory)

    spec_filename = '{0:s}.spec'.format(project_name)
    output_file_path = os.path.join(self._rpmbuild_specs_path, spec_filename)

    if not spec_file_generator.RewriteSetupPyGeneratedFile(
        self._project_definition, source_directory, source_filename,
        project_name, project_version, input_file_path, output_file_path):
      return

    return output_file_path

  def _MoveRPMs(self, project_name, project_version):
    """Moves the rpms from the rpmbuild directory into the current directory.

    Args:
      project_name (str): name of the project.
      project_version (str): version of the project.
    """
    filenames_glob = 'python*-{0:s}-*{1!s}-1.{2:s}.rpm'.format(
        project_name, project_version, self.architecture)
    filenames_glob = os.path.join(
        self._rpmbuild_rpms_path, self.architecture, filenames_glob)

    self._MoveFilesToCurrentDirectory(filenames_glob)

    filenames_glob = '{0:s}-*{1!s}-1.{2:s}.rpm'.format(
        project_name, project_version, self.architecture)
    filenames_glob = os.path.join(
        self._rpmbuild_rpms_path, self.architecture, filenames_glob)

    self._MoveFilesToCurrentDirectory(filenames_glob)

  def Build(self, source_helper_object):
    """Builds the rpms.

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

    logging.info('Building rpm of: {0:s}'.format(source_filename))

    project_name, project_version = self._GetFilenameSafeProjectInformation(
        source_helper_object)

    self._CopySourcePackageToRPMBuildSources(source_filename)

    rpm_spec_file_path = self._GenerateSpecFile(
        project_name, project_version, source_filename, source_helper_object)
    if not rpm_spec_file_path:
      logging.error('Unable to generate rpm spec file.')
      return False

    build_successful = self._BuildFromSpecFile(
        rpm_spec_file_path, rpmbuild_flags='-bb')

    if build_successful:
      self._MoveRPMs(project_name, project_version)
      self._RemoveBuildDirectory(project_name, project_version)

    return build_successful

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

    # Remove previous versions of rpms.
    project_name, project_version = self._GetFilenameSafeProjectInformation(
        source_helper_object)

    self._RemoveOlderBuildDirectory(project_name, project_version)
    self._RemoveOlderRPMs(project_name, project_version)


class SRPMBuildHelper(BaseRPMBuildHelper):
  """Helper to build source RPM packages (.src.rpm)."""

  def _MoveRPMs(self, project_name, project_version):
    """Moves the rpms from the rpmbuild directory into the current directory.

    Args:
      project_name (str): name of the project.
      project_version (str): version of the project.
    """
    filenames_glob = '{0:s}-*{1!s}-1.src.rpm'.format(
        project_name, project_version)
    filenames_glob = os.path.join(self._rpmbuild_srpms_path, filenames_glob)

    self._MoveFilesToCurrentDirectory(filenames_glob)

  def _RemoveOlderSourceRPMs(self, project_name, project_version):
    """Removes previous versions of .src.rpm files.

    Args:
      project_name (str): name of the project.
      project_version (str): version of the project.
    """
    filenames_to_ignore = '{0:s}-.*{1!s}-1.src.rpm'.format(
        project_name, project_version)
    filenames_to_ignore = re.compile(filenames_to_ignore)

    src_rpm_filenames_glob = '{0:s}-*-1.src.rpm'.format(project_name)
    filenames = glob.glob(src_rpm_filenames_glob)

    for filename in filenames:
      if not filenames_to_ignore.match(filename):
        logging.info('Removing: {0:s}'.format(filename))
        os.remove(filename)

    filenames_glob = os.path.join(
        self.rpmbuild_path, 'SRPMS', src_rpm_filenames_glob)
    filenames = glob.glob(filenames_glob)

    for filename in filenames:
      if not filenames_to_ignore.match(filename):
        logging.info('Removing: {0:s}'.format(filename))
        os.remove(filename)

  def CheckBuildRequired(self, source_helper_object):
    """Checks if a build is required.

    Args:
      source_helper_object (SourceHelper): source helper.

    Returns:
      bool: True if a build is required, False otherwise.
    """
    project_name, project_version = self._GetFilenameSafeProjectInformation(
        source_helper_object)

    srpm_filename = '{0:s}-{1!s}-1.src.rpm'.format(
        project_name, project_version)

    return not os.path.exists(srpm_filename)

  def Clean(self, source_helper_object):
    """Cleans the rpmbuild directory.

    Args:
      source_helper_object (SourceHelper): source helper.
    """
    project_name, project_version = self._GetFilenameSafeProjectInformation(
        source_helper_object)

    self._RemoveOlderSourceRPMs(project_name, project_version)


class ConfigureMakeSRPMBuildHelper(SRPMBuildHelper):
  """Helper to build source RPM packages (.src.rpm)."""

  def Build(self, source_helper_object):
    """Builds the source rpm.

    Args:
      source_helper_object (SourceHelper): source helper.

    Returns:
      bool: True if successful, False otherwise.
    """
    source_package_filename = source_helper_object.Download()
    if not source_package_filename:
      logging.info('Download of: {0:s} failed'.format(
          source_helper_object.project_name))
      return False

    logging.info('Building source rpm of: {0:s}'.format(
        source_package_filename))

    project_name, project_version = self._GetFilenameSafeProjectInformation(
        source_helper_object)

    # rpmbuild wants the source package filename without the status indication.
    rpm_source_package_filename = '{0:s}-{1!s}.tar.gz'.format(
        project_name, project_version)
    os.rename(source_package_filename, rpm_source_package_filename)

    build_successful = self._BuildFromSourcePackage(
        rpm_source_package_filename, rpmbuild_flags='-ts')

    # TODO: test binary build of source package?

    if build_successful:
      self._MoveRPMs(project_name, project_version)

    # Change the source package filename back to the original.
    os.rename(rpm_source_package_filename, source_package_filename)

    return build_successful


class SetupPySRPMBuildHelper(SRPMBuildHelper):
  """Helper to build source RPM packages (.src.rpm)."""

  def __init__(self, project_definition, l2tdevtools_path):
    """Initializes a build helper.

    Args:
      project_definition (ProjectDefinition): project definition.
      l2tdevtools_path (str): path to the l2tdevtools directory.
    """
    super(SetupPySRPMBuildHelper, self).__init__(
        project_definition, l2tdevtools_path)
    if not project_definition.architecture_dependent:
      self.architecture = 'noarch'

  def _GenerateSpecFile(
      self, project_name, project_version, source_filename,
      source_helper_object):
    """Generates the rpm spec file.

    Args:
      project_name (str): name of the project.
      project_version (str): version of the project.
      source_filename (str): name of the source package file.
      source_helper_object (SourceHelper): source helper.

    Returns:
      str: path of the generated rpm spec file or None.
    """
    source_directory = source_helper_object.Create()
    if not source_directory:
      logging.error(
          'Extraction of source package: {0:s} failed'.format(source_filename))
      return

    spec_file_generator = spec_file.RPMSpecFileGenerator(self._data_path)

    log_file_path = os.path.join('..', self.LOG_FILENAME)
    if not spec_file_generator.GenerateWithSetupPy(
        source_directory, log_file_path):
      return

    if project_name.startswith('python-'):
      project_name = project_name[7:]

    input_file_path = self._GetSetupPySpecFilePath(
        source_helper_object, source_directory)

    spec_filename = '{0:s}.spec'.format(project_name)
    output_file_path = os.path.join(self._rpmbuild_specs_path, spec_filename)

    if not spec_file_generator.RewriteSetupPyGeneratedFile(
        self._project_definition, source_directory, source_filename,
        project_name, project_version, input_file_path, output_file_path):
      return

    return output_file_path

  def Build(self, source_helper_object):
    """Builds the source rpm.

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

    logging.info('Building source rpm of: {0:s}'.format(source_filename))

    project_name, project_version = self._GetFilenameSafeProjectInformation(
        source_helper_object)

    self._CopySourcePackageToRPMBuildSources(source_filename)

    rpm_spec_file_path = self._GenerateSpecFile(
        project_name, project_version, source_filename, source_helper_object)
    if not rpm_spec_file_path:
      logging.error('Unable to generate rpm spec file.')
      return False

    build_successful = self._BuildFromSpecFile(
        rpm_spec_file_path, rpmbuild_flags='-bs')

    # TODO: test binary build of source package?

    if build_successful:
      self._MoveRPMs(project_name, project_version)

    return build_successful
