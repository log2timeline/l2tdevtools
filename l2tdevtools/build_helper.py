# -*- coding: utf-8 -*-
"""Build helper object implementations."""

from __future__ import print_function
import fileinput
import glob
import logging
import os
import platform
import re
import shutil
import subprocess
import sys

from l2tdevtools import dpkg_files


class BuildHelper(object):
  """Base class that helps in building."""

  LOG_FILENAME = u'build.log'

  def __init__(self, dependency_definition, data_path):
    """Initializes the build helper.

    Args:
      dependency_definition: the dependency definition object (instance of
                             DependencyDefinition).
      data_path: the path to the data directory which contains the patches
                 sub directory.
    """
    super(BuildHelper, self).__init__()
    self._data_path = data_path
    self._dependency_definition = dependency_definition


class DpkgBuildHelper(BuildHelper):
  """Class that helps in building dpkg packages (.deb)."""

  # TODO: determine BUILD_DEPENDENCIES from the build files?
  _BUILD_DEPENDENCIES = frozenset([
      u'git',
      u'build-essential',
      u'autotools-dev',
      u'autoconf',
      u'automake',
      u'autopoint',
      u'libtool',
      u'gettext',
      u'flex',
      u'byacc',
      u'debhelper',
      u'devscripts',
      u'dpkg-dev',
      u'fakeroot',
      u'quilt',
      u'libbz2-dev',
      u'libssl-dev',
      u'libfuse-dev',
      u'python-dev',
      u'python-setuptools',
      u'libsqlite3-dev',
  ])

  def __init__(self, dependency_definition, data_path):
    """Initializes the build helper.

    Args:
      dependency_definition: the dependency definition object (instance of
                             DependencyDefinition).
      data_path: the path to the data directory which contains the patches
                 sub directory.
    """
    super(DpkgBuildHelper, self).__init__(dependency_definition, data_path)
    self._prep_script = u'prep-dpkg.sh'
    self._post_script = u'post-dpkg.sh'

  def _BuildPrepare(
      self, source_directory, project_name, project_version, version_suffix,
      distribution, architecture):
    """Make the necessary preparations before building the dpkg packages.

    Args:
      source_directory: the name of the source directory.
      project_name: the name of the project.
      project_version: the version of the project.
      version_suffix: the version suffix.
      distribution: the distribution.
      architecture: the architecture.

    Returns:
      True if the preparations were successful, False otherwise.
    """
    # Script to run before building, e.g. to change the dpkg packaging files.
    if os.path.exists(self._prep_script):
      command = u'sh ../{0:s} {1:s} {2!s} {3:s} {4:s} {5:s}'.format(
          self._prep_script, project_name, project_version, version_suffix,
          distribution, architecture)
      exit_code = subprocess.call(
          u'(cd {0:s} && {1:s})'.format(source_directory, command), shell=True)
      if exit_code != 0:
        logging.error(u'Running: "{0:s}" failed.'.format(command))
        return False

    return True

  def _BuildFinalize(
      self, source_directory, project_name, project_version, version_suffix,
      distribution, architecture):
    """Make the necessary finalizations after building the dpkg packages.

    Args:
      source_directory: the name of the source directory.
      project_name: the name of the project.
      project_version: the version of the project.
      version_suffix: the version suffix.
      distribution: the distribution.
      architecture: the architecture.

    Returns:
      True if the finalizations were successful, False otherwise.
    """
    # Script to run after building, e.g. to automatically upload the dpkg
    # package files to an apt repository.
    if os.path.exists(self._post_script):
      command = u'sh ../{0:s} {1:s} {2!s} {3:s} {4:s} {5:s}'.format(
          self._post_script, project_name, project_version, version_suffix,
          distribution, architecture)
      exit_code = subprocess.call(
          u'(cd {0:s} && {1:s})'.format(source_directory, command), shell=True)
      if exit_code != 0:
        logging.error(u'Running: "{0:s}" failed.'.format(command))
        return False

    return True

  @classmethod
  def CheckBuildDependencies(cls):
    """Checks if the build dependencies are met.

    Returns:
      A list of package names that need to be installed or an empty list.
    """
    missing_packages = []
    for package_name in cls._BUILD_DEPENDENCIES:
      if not cls.CheckIsInstalled(package_name):
        missing_packages.append(package_name)

    return missing_packages

  @classmethod
  def CheckIsInstalled(cls, package_name):
    """Checks if a package is installed.

    Args:
      package_name: the name of the package.

    Returns:
      A boolean value containing true if the package is installed
      false otherwise.
    """
    command = u'dpkg-query -s {0:s} >/dev/null 2>&1'.format(package_name)
    exit_code = subprocess.call(command, shell=True)
    return exit_code == 0


class ConfigureMakeDpkgBuildHelper(DpkgBuildHelper):
  """Class that helps in building dpkg packages (.deb)."""

  _VERSION_GLOB = u'[0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9]'

  def __init__(self, dependency_definition, data_path):
    """Initializes the build helper.

    Args:
      dependency_definition: the dependency definition object (instance of
                             DependencyDefinition).
      data_path: the path to the data directory which contains the patches
                 sub directory.
    """
    super(ConfigureMakeDpkgBuildHelper, self).__init__(
        dependency_definition, data_path)
    self.architecture = platform.machine()
    self.distribution = u''
    self.version_suffix = u''

    if self.architecture == u'i686':
      self.architecture = u'i386'
    elif self.architecture == u'x86_64':
      self.architecture = u'amd64'

  def Build(self, source_helper):
    """Builds the dpkg packages.

    Args:
      source_helper: the source helper (instance of SourceHelper).

    Returns:
      True if the build was successful, False otherwise.
    """
    source_filename = source_helper.Download()
    if not source_filename:
      logging.info(u'Download of: {0:s} failed'.format(
          source_helper.project_name))
      return False

    # dpkg-buildpackage wants an source package filename without
    # the status indication and orig indication.
    deb_orig_source_filename = u'{0:s}_{1!s}.orig.tar.gz'.format(
        source_helper.project_name, source_helper.project_version)
    shutil.copy(source_filename, deb_orig_source_filename)

    source_directory = source_helper.Create()
    if not source_directory:
      logging.error(
          u'Extraction of source package: {0:s} failed'.format(source_filename))
      return False

    logging.info(u'Building deb of: {0:s}'.format(source_filename))

    dpkg_directory = os.path.join(source_directory, u'dpkg')
    if not os.path.exists(dpkg_directory):
      dpkg_directory = os.path.join(source_directory, u'config', u'dpkg')

    if not os.path.exists(dpkg_directory):
      # Generate the dpkg build files if necessary.
      os.chdir(source_directory)

      build_files_generator = dpkg_files.DpkgBuildFilesGenerator(
          source_helper.project_name, source_helper.project_version,
          self._dependency_definition, self._data_path)
      build_files_generator.GenerateFiles(u'dpkg')

      os.chdir(u'..')

      dpkg_directory = os.path.join(source_directory, u'dpkg')

    if not os.path.exists(dpkg_directory):
      logging.error(u'Missing dpkg sub directory in: {0:s}'.format(
          source_directory))
      return False

    debian_directory = os.path.join(source_directory, u'debian')

    # If there is a debian directory remove it and recreate it from
    # the dpkg directory.
    if os.path.exists(debian_directory):
      logging.info(u'Removing: {0:s}'.format(debian_directory))
      shutil.rmtree(debian_directory)
    shutil.copytree(dpkg_directory, debian_directory)

    if not self._BuildPrepare(
        source_directory, source_helper.project_name,
        source_helper.project_version, self.version_suffix, self.distribution,
        self.architecture):
      return False

    command = u'dpkg-buildpackage -uc -us -rfakeroot > {0:s} 2>&1'.format(
        os.path.join(u'..', self.LOG_FILENAME))
    exit_code = subprocess.call(
        u'(cd {0:s} && {1:s})'.format(source_directory, command), shell=True)
    if exit_code != 0:
      logging.error(u'Running: "{0:s}" failed.'.format(command))
      return False

    if not self._BuildFinalize(
        source_directory, source_helper.project_name,
        source_helper.project_version, self.version_suffix, self.distribution,
        self.architecture):
      return False

    return True

  def Clean(self, source_helper):
    """Cleans the dpkg packages in the current directory.

    Args:
      source_helper: the source helper (instance of SourceHelper).
    """
    filenames_to_ignore = re.compile(u'^{0:s}_{1!s}.orig.tar.gz'.format(
        source_helper.project_name, source_helper.project_version))

    # Remove files of previous versions in the format:
    # project_version.orig.tar.gz
    filenames = glob.glob(u'{0:s}_{1:s}.orig.tar.gz'.format(
        source_helper.project_name, self._VERSION_GLOB))

    for filename in filenames:
      if not filenames_to_ignore.match(filename):
        logging.info(u'Removing: {0:s}'.format(filename))
        os.remove(filename)

    filenames_to_ignore = re.compile(u'^{0:s}[-_].*{1!s}'.format(
        source_helper.project_name, source_helper.project_version))

    # Remove files of previous versions in the format:
    # project[-_]version-1_architecture.*
    filenames = glob.glob(u'{0:s}[-_]*{1:s}-1_{2:s}.*'.format(
        source_helper.project_name, self._VERSION_GLOB, self.architecture))

    for filename in filenames:
      if not filenames_to_ignore.match(filename):
        logging.info(u'Removing: {0:s}'.format(filename))
        os.remove(filename)

    # Remove files of previous versions in the format:
    # project[-_]*version-1.*
    filenames = glob.glob(u'{0:s}[-_]*{1:s}-1.*'.format(
        source_helper.project_name, self._VERSION_GLOB))

    for filename in filenames:
      if not filenames_to_ignore.match(filename):
        logging.info(u'Removing: {0:s}'.format(filename))
        os.remove(filename)

  def GetOutputFilename(self, source_helper):
    """Retrieves the filename of one of the resulting files.

    Args:
      source_helper: the source helper (instance of SourceHelper).

    Returns:
      A filename of one of the resulting dpkg packages.
    """
    return u'{0:s}_{1!s}-1_{2:s}.deb'.format(
        source_helper.project_name, source_helper.project_version,
        self.architecture)


class ConfigureMakeSourceDpkgBuildHelper(DpkgBuildHelper):
  """Class that helps in building source dpkg packages (.deb)."""

  _VERSION_GLOB = u'[0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9]'

  def __init__(self, dependency_definition, data_path):
    """Initializes the build helper.

    Args:
      dependency_definition: the dependency definition object (instance of
                             DependencyDefinition).
      data_path: the path to the data directory which contains the patches
                 sub directory.
    """
    super(ConfigureMakeSourceDpkgBuildHelper, self).__init__(
        dependency_definition, data_path)
    self._prep_script = u'prep-dpkg-source.sh'
    self._post_script = u'post-dpkg-source.sh'
    self.architecture = u'source'
    self.distribution = u'trusty'
    self.version_suffix = u'ppa1'

  def Build(self, source_helper):
    """Builds the dpkg packages.

    Args:
      source_helper: the source helper (instance of SourceHelper).

    Returns:
      True if the build was successful, False otherwise.
    """
    source_filename = source_helper.Download()
    if not source_filename:
      logging.info(u'Download of: {0:s} failed'.format(
          source_helper.project_name))
      return False

    # dpkg-buildpackage wants an source package filename without
    # the status indication and orig indication.
    deb_orig_source_filename = u'{0:s}_{1!s}.orig.tar.gz'.format(
        source_helper.project_name, source_helper.project_version)
    shutil.copy(source_filename, deb_orig_source_filename)

    source_directory = source_helper.Create()
    if not source_directory:
      logging.error(
          u'Extraction of source package: {0:s} failed'.format(source_filename))
      return False

    logging.info(u'Building source deb of: {0:s}'.format(source_filename))

    dpkg_directory = os.path.join(source_directory, u'dpkg')
    if not os.path.exists(dpkg_directory):
      dpkg_directory = os.path.join(source_directory, u'config', u'dpkg')

    if not os.path.exists(dpkg_directory):
      # Generate the dpkg build files if necessary.
      os.chdir(source_directory)

      build_files_generator = dpkg_files.DpkgBuildFilesGenerator(
          source_helper.project_name, source_helper.project_version,
          self._dependency_definition, self._data_path)
      build_files_generator.GenerateFiles(u'dpkg')

      os.chdir(u'..')

      dpkg_directory = os.path.join(source_directory, u'dpkg')

    if not os.path.exists(dpkg_directory):
      logging.error(u'Missing dpkg sub directory in: {0:s}'.format(
          source_directory))
      return False

    debian_directory = os.path.join(source_directory, u'debian')

    # If there is a debian directory remove it and recreate it from
    # the dpkg directory.
    if os.path.exists(debian_directory):
      logging.info(u'Removing: {0:s}'.format(debian_directory))
      shutil.rmtree(debian_directory)
    shutil.copytree(dpkg_directory, debian_directory)

    if not self._BuildPrepare(
        source_directory, source_helper.project_name,
        source_helper.project_version, self.version_suffix, self.distribution,
        self.architecture):
      return False

    command = u'debuild -S -sa > {0:s} 2>&1'.format(
        os.path.join(u'..', self.LOG_FILENAME))
    exit_code = subprocess.call(
        u'(cd {0:s} && {1:s})'.format(source_directory, command), shell=True)
    if exit_code != 0:
      logging.error(u'Running: "{0:s}" failed.'.format(command))
      return False

    if not self._BuildFinalize(
        source_directory, source_helper.project_name,
        source_helper.project_version, self.version_suffix, self.distribution,
        self.architecture):
      return False

    return True

  def Clean(self, source_helper):
    """Cleans the dpkg packages in the current directory.

    Args:
      source_helper: the source helper (instance of SourceHelper).
    """
    filenames_to_ignore = re.compile(u'^{0:s}_{1!s}.orig.tar.gz'.format(
        source_helper.project_name, source_helper.project_version))

    # Remove files of previous versions in the format:
    # project_version.orig.tar.gz
    filenames = glob.glob(u'{0:s}_{1:s}.orig.tar.gz'.format(
        source_helper.project_name, self._VERSION_GLOB))

    for filename in filenames:
      if not filenames_to_ignore.match(filename):
        logging.info(u'Removing: {0:s}'.format(filename))
        os.remove(filename)

    filenames_to_ignore = re.compile(u'^{0:s}[-_].*{1!s}'.format(
        source_helper.project_name, source_helper.project_version))

    # Remove files of previous versions in the format:
    # project[-_]version-1suffix~distribution_architecture.*
    filenames = glob.glob((u'{0:s}[-_]*{1:s}-1{2:s}~{3:s}_{4:s}.*').format(
        source_helper.project_name, self._VERSION_GLOB, self.version_suffix,
        self.distribution, self.architecture))

    for filename in filenames:
      if not filenames_to_ignore.match(filename):
        logging.info(u'Removing: {0:s}'.format(filename))
        os.remove(filename)

    # Remove files of previous versions in the format:
    # project[-_]*version-1suffix~distribution.*
    filenames = glob.glob((u'{0:s}[-_]*{1:s}-1{2:s}~{3:s}.*').format(
        source_helper.project_name, self._VERSION_GLOB, self.version_suffix,
        self.distribution))

    for filename in filenames:
      if not filenames_to_ignore.match(filename):
        logging.info(u'Removing: {0:s}'.format(filename))
        os.remove(filename)

  def GetOutputFilename(self, source_helper):
    """Retrieves the filename of one of the resulting files.

    Args:
      source_helper: the source helper (instance of SourceHelper).

    Returns:
      A filename of one of the resulting dpkg packages.
    """
    return u'{0:s}_{1!s}-1{2:s}~{3:s}_{4:s}.changes'.format(
        source_helper.project_name, source_helper.project_version,
        self.version_suffix, self.distribution, self.architecture)


class SetupPyDpkgBuildHelper(DpkgBuildHelper):
  """Class that helps in building dpkg packages (.deb)."""

  def __init__(self, dependency_definition, data_path):
    """Initializes the build helper.

    Args:
      dependency_definition: the dependency definition object (instance of
                             DependencyDefinition).
      data_path: the path to the data directory which contains the patches
                 sub directory.
    """
    super(SetupPyDpkgBuildHelper, self).__init__(
        dependency_definition, data_path)
    self.architecture = platform.machine()
    self.distribution = u''
    self.version_suffix = u''

    if not dependency_definition.architecture_dependent:
      self.architecture = u'all'
    elif self.architecture == u'i686':
      self.architecture = u'i386'
    elif self.architecture == u'x86_64':
      self.architecture = u'amd64'

  def Build(self, source_helper):
    """Builds the dpkg packages.

    Args:
      source_helper: the source helper (instance of SourceHelper).

    Returns:
      True if the build was successful, False otherwise.
    """
    source_filename = source_helper.Download()
    if not source_filename:
      logging.info(u'Download of: {0:s} failed'.format(
          source_helper.project_name))
      return False

    project_name = source_helper.project_name
    if project_name.startswith(u'python-'):
      project_name = project_name[7:]

    # dpkg-buildpackage wants an source package filename without
    # the status indication and orig indication.
    deb_orig_source_filename = u'python-{0:s}_{1!s}.orig.tar.gz'.format(
        project_name, source_helper.project_version)
    shutil.copy(source_filename, deb_orig_source_filename)

    source_directory = source_helper.Create()
    if not source_directory:
      logging.error(
          u'Extraction of source package: {0:s} failed'.format(source_filename))
      return False

    logging.info(u'Building deb of: {0:s}'.format(source_filename))

    dpkg_directory = os.path.join(source_directory, u'dpkg')
    if not os.path.exists(dpkg_directory):
      dpkg_directory = os.path.join(source_directory, u'config', u'dpkg')

    if not os.path.exists(dpkg_directory):
      # Generate the dpkg build files if necessary.
      os.chdir(source_directory)

      build_files_generator = dpkg_files.DpkgBuildFilesGenerator(
          project_name, source_helper.project_version,
          self._dependency_definition, self._data_path)
      build_files_generator.GenerateFiles(u'dpkg')

      os.chdir(u'..')

      dpkg_directory = os.path.join(source_directory, u'dpkg')

    if not os.path.exists(dpkg_directory):
      logging.error(u'Missing dpkg sub directory in: {0:s}'.format(
          source_directory))
      return False

    debian_directory = os.path.join(source_directory, u'debian')

    # If there is a debian directory remove it and recreate it from
    # the dpkg directory.
    if os.path.exists(debian_directory):
      logging.info(u'Removing: {0:s}'.format(debian_directory))
      shutil.rmtree(debian_directory)
    shutil.copytree(dpkg_directory, debian_directory)

    if not self._BuildPrepare(
        source_directory, project_name, source_helper.project_version,
        self.version_suffix, self.distribution, self.architecture):
      return False

    command = u'dpkg-buildpackage -uc -us -rfakeroot > {0:s} 2>&1'.format(
        os.path.join(u'..', self.LOG_FILENAME))
    exit_code = subprocess.call(
        u'(cd {0:s} && {1:s})'.format(source_directory, command), shell=True)
    if exit_code != 0:
      logging.error(u'Running: "{0:s}" failed.'.format(command))
      return False

    if not self._BuildFinalize(
        source_directory, project_name, source_helper.project_version,
        self.version_suffix, self.distribution, self.architecture):
      return False

    return True

  def Clean(self, source_helper):
    """Cleans the dpkg packages in the current directory.

    Args:
      source_helper: the source helper (instance of SourceHelper).
    """
    if self._dependency_definition.dpkg_name:
      project_name = self._dependency_definition.dpkg_name
    else:
      project_name = source_helper.project_name
      if project_name.startswith(u'python-'):
        project_name = project_name[7:]

    filenames_to_ignore = re.compile(u'^python-{0:s}_{1!s}.orig.tar.gz'.format(
        project_name, source_helper.project_version))

    # Remove files of previous versions in the format:
    # python-project_version.orig.tar.gz
    filenames = glob.glob(u'python-{0:s}_*.orig.tar.gz'.format(project_name))

    for filename in filenames:
      if not filenames_to_ignore.match(filename):
        logging.info(u'Removing: {0:s}'.format(filename))
        os.remove(filename)

    filenames_to_ignore = re.compile(u'^python-{0:s}[-_].*{1!s}'.format(
        project_name, source_helper.project_version))

    # Remove files of previous versions in the format:
    # python-project[-_]*version-1_architecture.*
    filenames = glob.glob(u'python-{0:s}[-_]*-1_{1:s}.*'.format(
        project_name, self.architecture))

    for filename in filenames:
      if not filenames_to_ignore.match(filename):
        logging.info(u'Removing: {0:s}'.format(filename))
        os.remove(filename)

    # Remove files of previous versions in the format:
    # python-project[-_]*version-1.*
    filenames = glob.glob(u'python-{0:s}[-_]*-1.*'.format(project_name))

    for filename in filenames:
      if not filenames_to_ignore.match(filename):
        logging.info(u'Removing: {0:s}'.format(filename))
        os.remove(filename)

  def GetOutputFilename(self, source_helper):
    """Retrieves the filename of one of the resulting files.

    Args:
      source_helper: the source helper (instance of SourceHelper).

    Returns:
      A filename of one of the resulting dpkg packages.
    """
    if self._dependency_definition.dpkg_name:
      project_name = self._dependency_definition.dpkg_name
    else:
      project_name = source_helper.project_name
      if project_name.startswith(u'python-'):
        project_name = project_name[7:]

    return u'python-{0:s}_{1!s}-1_{2:s}.deb'.format(
        project_name, source_helper.project_version, self.architecture)


class SetupPySourceDpkgBuildHelper(DpkgBuildHelper):
  """Class that helps in building source dpkg packages (.deb)."""

  def __init__(self, dependency_definition, data_path):
    """Initializes the build helper.

    Args:
      dependency_definition: the dependency definition object (instance of
                             DependencyDefinition).
      data_path: the path to the data directory which contains the patches
                 sub directory.
    """
    super(SetupPySourceDpkgBuildHelper, self).__init__(
        dependency_definition, data_path)
    self._prep_script = u'prep-dpkg-source.sh'
    self._post_script = u'post-dpkg-source.sh'
    self.architecture = u'source'
    self.distribution = u'trusty'
    self.version_suffix = u'ppa1'

  def Build(self, source_helper):
    """Builds the dpkg packages.

    Args:
      source_helper: the source helper (instance of SourceHelper).

    Returns:
      True if the build was successful, False otherwise.
    """
    source_filename = source_helper.Download()
    if not source_filename:
      logging.info(u'Download of: {0:s} failed'.format(
          source_helper.project_name))
      return False

    project_name = source_helper.project_name
    if project_name.startswith(u'python-'):
      project_name = project_name[7:]

    # dpkg-buildpackage wants an source package filename without
    # the status indication and orig indication.
    deb_orig_source_filename = u'python-{0:s}_{1!s}.orig.tar.gz'.format(
        project_name, source_helper.project_version)
    shutil.copy(source_filename, deb_orig_source_filename)

    source_directory = source_helper.Create()
    if not source_directory:
      logging.error(
          u'Extraction of source package: {0:s} failed'.format(source_filename))
      return False

    logging.info(u'Building source deb of: {0:s}'.format(source_filename))

    dpkg_directory = os.path.join(source_directory, u'dpkg')
    if not os.path.exists(dpkg_directory):
      dpkg_directory = os.path.join(source_directory, u'config', u'dpkg')

    if not os.path.exists(dpkg_directory):
      # Generate the dpkg build files if necessary.
      os.chdir(source_directory)

      build_files_generator = dpkg_files.DpkgBuildFilesGenerator(
          project_name, source_helper.project_version,
          self._dependency_definition, self._data_path)
      build_files_generator.GenerateFiles(u'dpkg')

      os.chdir(u'..')

      dpkg_directory = os.path.join(source_directory, u'dpkg')

    if not os.path.exists(dpkg_directory):
      logging.error(u'Missing dpkg sub directory in: {0:s}'.format(
          source_directory))
      return False

    debian_directory = os.path.join(source_directory, u'debian')

    # If there is a debian directory remove it and recreate it from
    # the dpkg directory.
    if os.path.exists(debian_directory):
      logging.info(u'Removing: {0:s}'.format(debian_directory))
      shutil.rmtree(debian_directory)
    shutil.copytree(dpkg_directory, debian_directory)

    if not self._BuildPrepare(
        source_directory, project_name, source_helper.project_version,
        self.version_suffix, self.distribution, self.architecture):
      return False

    command = u'debuild -S -sa > {0:s} 2>&1'.format(
        os.path.join(u'..', self.LOG_FILENAME))
    exit_code = subprocess.call(
        u'(cd {0:s} && {1:s})'.format(source_directory, command), shell=True)
    if exit_code != 0:
      logging.error(u'Running: "{0:s}" failed.'.format(command))
      return False

    if not self._BuildFinalize(
        source_directory, project_name, source_helper.project_version,
        self.version_suffix, self.distribution, self.architecture):
      return False

    return True

  def Clean(self, source_helper):
    """Cleans the dpkg packages in the current directory.

    Args:
      source_helper: the source helper (instance of SourceHelper).
    """
    if self._dependency_definition.dpkg_name:
      project_name = self._dependency_definition.dpkg_name
    else:
      project_name = source_helper.project_name
      if project_name.startswith(u'python-'):
        project_name = project_name[7:]

    filenames_to_ignore = re.compile(u'^python-{0:s}_{1!s}.orig.tar.gz'.format(
        project_name, source_helper.project_version))

    # Remove files of previous versions in the format:
    # python-project_version.orig.tar.gz
    filenames = glob.glob(u'python-{0:s}_*.orig.tar.gz'.format(project_name))

    for filename in filenames:
      if not filenames_to_ignore.match(filename):
        logging.info(u'Removing: {0:s}'.format(filename))
        os.remove(filename)

    filenames_to_ignore = re.compile(u'^python-{0:s}[-_].*{1!s}'.format(
        project_name, source_helper.project_version))

    # Remove files of previous versions in the format:
    # python-project[-_]*version-1suffix~distribution_architecture.*
    filenames = glob.glob(u'python-{0:s}[-_]*-1{1:s}~{2:s}_{3:s}.*'.format(
        project_name, self.version_suffix, self.distribution,
        self.architecture))

    for filename in filenames:
      if not filenames_to_ignore.match(filename):
        logging.info(u'Removing: {0:s}'.format(filename))
        os.remove(filename)

    # Remove files of previous versions in the format:
    # python-project[-_]*version-1suffix~distribution.*
    filenames = glob.glob(u'python-{0:s}[-_]*-1{1:s}~{2:s}.*'.format(
        project_name, self.version_suffix, self.distribution))

    for filename in filenames:
      if not filenames_to_ignore.match(filename):
        logging.info(u'Removing: {0:s}'.format(filename))
        os.remove(filename)

  def GetOutputFilename(self, source_helper):
    """Retrieves the filename of one of the resulting files.

    Args:
      source_helper: the source helper (instance of SourceHelper).

    Returns:
      A filename of one of the resulting dpkg packages.
    """
    if self._dependency_definition.dpkg_name:
      project_name = self._dependency_definition.dpkg_name
    else:
      project_name = source_helper.project_name
      if project_name.startswith(u'python-'):
        project_name = project_name[7:]

    return u'python-{0:s}_{1!s}-1{2:s}~{3:s}_{4:s}.changes'.format(
        project_name, source_helper.project_version,
        self.version_suffix, self.distribution, self.architecture)


class MsiBuildHelper(BuildHelper):
  """Class that helps in building Microsoft Installer packages (.msi)."""

  def __init__(self, dependency_definition, data_path):
    """Initializes the build helper.

    Args:
      dependency_definition: the dependency definition object (instance of
                             DependencyDefinition).
      data_path: the path to the data directory which contains the patches
                 sub directory.
    """
    super(MsiBuildHelper, self).__init__(dependency_definition, data_path)
    self.architecture = platform.machine()

    if self.architecture == u'x86':
      self.architecture = u'win32'
    elif self.architecture == u'AMD64':
      self.architecture = u'win-amd64'


class ConfigureMakeMsiBuildHelper(MsiBuildHelper):
  """Class that helps in building Microsoft Installer packages (.msi)."""

  def __init__(self, dependency_definition, data_path, tools_path):
    """Initializes the build helper.

    Args:
      dependency_definition: the dependency definition object (instance of
                             DependencyDefinition).
      data_path: the path to the data directory which contains the patches
                 sub directory.
      tools_path: the path to the tools directory which contains the
                  msvscpp-convert.py script.

    Raises:
      RuntimeError: if the Visual Studio version could be determined or
                    msvscpp-convert.py could not be found.
    """
    super(ConfigureMakeMsiBuildHelper, self).__init__(
        dependency_definition, data_path)

    if 'VS120COMNTOOLS' in os.environ:
      self.version = '2013'

    elif 'VS110COMNTOOLS' in os.environ:
      self.version = '2012'

    elif 'VS100COMNTOOLS' in os.environ:
      self.version = '2010'

    # Since the script exports VS90COMNTOOLS to the environment we need
    # to check the other Visual Studio environment variables first.
    elif 'VS90COMNTOOLS' in os.environ:
      self.version = '2008'

    else:
      raise RuntimeError(u'Unable to determine Visual Studio version.')

    if self.version != '2008':
      self._msvscpp_convert = os.path.join(tools_path, u'msvscpp-convert.py')

      if not os.path.exists(self._msvscpp_convert):
        raise RuntimeError(u'Unable to find msvscpp-convert.py')

  def _BuildPrepare(self, source_helper, source_directory):
    """Prepares the source for building with Visual Studio.

    Args:
      source_helper: the source helper (instance of SourceHelper).
      source_directory: the name of the source directory.
    """
    # For the vs2008 build make sure the binary is XP compatible,
    # by setting WINVER to 0x0501. For the vs2010 build WINVER is
    # set to 0x0600 (Windows Vista).

    # WINVER is set in common\config_winapi.h or common\config_msc.h.
    config_filename = os.path.join(
        source_directory, u'common', u'config_winapi.h')

    # If the WINAPI configuration file is not available use
    # the MSC compiler configuration file instead.
    if not os.path.exists(config_filename):
      config_filename = os.path.join(
          source_directory, u'common', u'config_msc.h')

    # Add a line to the config file that sets WINVER.
    parsing_mode = 0

    for line in fileinput.input(config_filename, inplace=1):
      # Remove trailing whitespace and end-of-line characters.
      line = line.rstrip()

      if parsing_mode != 2 or line:
        if parsing_mode == 1:
          # TODO: currently we want libbde not use Windows Crypto API, hence
          # we set WINVER to 0x0501.
          if self.version == '2008' or source_helper.project_name == 'libbde':
            if not line.startswith('#define WINVER 0x0501'):
              print('#define WINVER 0x0501')
              print('')

          else:
            if not line.startswith('#define WINVER 0x0600'):
              print('#define WINVER 0x0600')
              print('')

          parsing_mode = 2

        elif line.startswith('#define _CONFIG_'):
          parsing_mode = 1

      print(line)

  def _ConvertSolutionFiles(self, source_directory):
    """Converts the Visual Studio solution and project files.

    Args:
      source_directory: the name of the source directory.
    """
    logging.info(u'Converting Visual Studio solution and project files.')
    os.chdir(source_directory)

    solution_filenames = glob.glob(os.path.join(u'msvscpp', u'*.sln'))
    if len(solution_filenames) != 1:
      logging.error(u'Unable to find Visual Studio solution file')
      return False

    solution_filename = solution_filenames[0]

    if not os.path.exists(u'vs2008'):
      command = u'{0:s} {1:s} --to {2:s} {3:s}'.format(
          sys.executable, self._msvscpp_convert, self.version,
          solution_filename)
      exit_code = subprocess.call(command, shell=False)
      if exit_code != 0:
        logging.error(u'Running: "{0:s}" failed.'.format(command))
        return False

      # Note that setup.py needs the Visual Studio solution directory
      # to be named: msvscpp. So replace the Visual Studio 2008 msvscpp
      # solution directory with the converted one.
      os.rename(u'msvscpp', u'vs2008')
      os.rename(u'vs{0:s}'.format(self.version), u'msvscpp')

    os.chdir(u'..')

  def Build(self, source_helper):
    """Builds using Visual Studio.

    Args:
      source_helper: the source helper (instance of SourceHelper).

    Returns:
      True if the build was successful, False otherwise.
    """
    source_filename = source_helper.Download()
    if not source_filename:
      logging.info(u'Download of: {0:s} failed'.format(
          source_helper.project_name))
      return False

    source_directory = source_helper.Create()
    if not source_directory:
      logging.error(
          u'Extraction of source package: {0:s} failed'.format(source_filename))
      return False

    logging.info(u'Building: {0:s} with Visual Studio {1:s}'.format(
        source_filename, self.version))

    # Search common locations for MSBuild.exe
    if self.version == '2008':
      msbuild = u'{0:s}:{1:s}{2:s}'.format(
          u'C', os.sep, os.path.join(
              u'Windows', u'Microsoft.NET', u'Framework', u'v3.5',
              u'MSBuild.exe'))

    # Note that MSBuild in .NET 3.5 does not support vs2010 solution files
    # and MSBuild in .NET 4.0 is needed instead.
    elif self.version in ['2010', '2012', '2013']:
      msbuild = u'{0:s}:{1:s}{2:s}'.format(
          u'C', os.sep, os.path.join(
              u'Windows', u'Microsoft.NET', u'Framework', u'v4.0.30319',
              u'MSBuild.exe'))

    if not os.path.exists(msbuild):
      logging.error(u'Unable to find MSBuild.exe')
      return False

    if self.version == '2008':
      if not os.environ['VS90COMNTOOLS']:
        logging.error(u'Missing VS90COMNTOOLS environment variable.')
        return False

    elif self.version == '2010':
      if not os.environ['VS100COMNTOOLS']:
        logging.error(u'Missing VS100COMNTOOLS environment variable.')
        return False

    elif self.version == '2012':
      if not os.environ['VS110COMNTOOLS']:
        logging.error(u'Missing VS110COMNTOOLS environment variable.')
        return False

    elif self.version == '2013':
      if not os.environ['VS120COMNTOOLS']:
        logging.error(u'Missing VS120COMNTOOLS environment variable.')
        return False

    zlib_project_file = os.path.join(
        source_directory, u'msvscpp', u'zlib', u'zlib.vcproj')
    zlib_source_directory = os.path.join(
        os.path.dirname(source_directory), u'zlib')

    if (os.path.exists(zlib_project_file) and
        not os.path.exists(zlib_source_directory)):
      logging.error(u'Missing dependency: zlib.')
      return False

    dokan_project_file = os.path.join(
        source_directory, u'msvscpp', u'dokan', u'dokan.vcproj')
    dokan_source_directory = os.path.join(
        os.path.dirname(source_directory), u'dokan')

    if (os.path.exists(dokan_project_file) and
        not os.path.exists(dokan_source_directory)):
      logging.error(u'Missing dependency: dokan.')
      return False

    # For the Visual Studio builds later than 2008 the convert the 2008
    # solution and project files need to be converted to the newer version.
    if self.version in ['2010', '2012', '2013']:
      self._ConvertSolutionFiles(source_directory)

    self._BuildPrepare(source_helper, source_directory)

    # Detect architecture based on Visual Studion Platform environment
    # variable. If not set the platform with default to Win32.
    msvscpp_platform = os.environ.get('Platform', None)
    if not msvscpp_platform:
      msvscpp_platform = os.environ.get('TARGET_CPU', None)

    if not msvscpp_platform or msvscpp_platform == 'x86':
      msvscpp_platform = 'Win32'

    if msvscpp_platform not in ['Win32', 'x64']:
      logging.error(u'Unsupported build platform: {0:s}'.format(
          msvscpp_platform))
      return False

    if self.version == '2008' and msvscpp_platform == 'x64':
      logging.error(u'Unsupported 64-build platform for vs2008.')
      return False

    solution_filenames = glob.glob(os.path.join(
        source_directory, u'msvscpp', u'*.sln'))
    if len(solution_filenames) != 1:
      logging.error(u'Unable to find Visual Studio solution file')
      return False

    solution_filename = solution_filenames[0]

    command = (
        u'{0:s} /p:Configuration=Release /p:Platform={1:s} /noconsolelogger '
        u'/fileLogger /maxcpucount {2:s}').format(
            msbuild, msvscpp_platform, solution_filename)
    exit_code = subprocess.call(command, shell=False)
    if exit_code != 0:
      logging.error(u'Running: "{0:s}" failed.'.format(command))
      return False

    python_module_name, _, _ = source_directory.partition(u'-')
    python_module_name = u'py{0:s}'.format(python_module_name[3:])
    python_module_directory = os.path.join(
        source_directory, python_module_name)
    python_module_dist_directory = os.path.join(
        python_module_directory, u'dist')

    if not os.path.exists(python_module_dist_directory):
      build_directory = os.path.join(u'..', u'..')

      os.chdir(python_module_directory)

      # Setup.py uses VS90COMNTOOLS which is vs2008 specific
      # so we need to set it for the other Visual Studio versions.
      if self.version == '2010':
        os.environ['VS90COMNTOOLS'] = os.environ['VS100COMNTOOLS']

      elif self.version == '2012':
        os.environ['VS90COMNTOOLS'] = os.environ['VS110COMNTOOLS']

      elif self.version == '2013':
        os.environ['VS90COMNTOOLS'] = os.environ['VS120COMNTOOLS']

      command = u'{0:s} setup.py bdist_msi'.format(sys.executable)
      exit_code = subprocess.call(command, shell=False)
      if exit_code != 0:
        logging.error(u'Running: "{0:s}" failed.'.format(command))
        return False

      # Move the msi to the build directory.
      msi_filename = glob.glob(os.path.join(
          u'dist', u'{0:s}-*.msi'.format(python_module_name)))

      logging.info(u'Moving: {0:s}'.format(msi_filename[0]))
      shutil.move(msi_filename[0], build_directory)

      os.chdir(build_directory)

    return True

  def Clean(self, source_helper):
    """Cleans the build and dist directory.

    Args:
      source_helper: the source helper (instance of SourceHelper).
    """
    # Remove previous versions of MSIs.
    filenames_to_ignore = re.compile(
        u'py{0:s}-.*{1!s}.1.{2:s}-py2.7.msi'.format(
            source_helper.project_name[3:], source_helper.project_version,
            self.architecture))

    msi_filenames_glob = u'py{0:s}-*.1.{1:s}-py2.7.msi'.format(
        source_helper.project_name[3:], self.architecture)

    filenames = glob.glob(msi_filenames_glob)
    for filename in filenames:
      if not filenames_to_ignore.match(filename):
        logging.info(u'Removing: {0:s}'.format(filename))
        os.remove(filename)

  def GetOutputFilename(self, source_helper):
    """Retrieves the filename of one of the resulting files.

    Args:
      source_helper: the source helper (instance of SourceHelper).

    Returns:
      A filename of one of the resulting MSIs.
    """
    return u'{0:s}-{1!s}.1.{2:s}-py2.7.msi'.format(
        source_helper.project_name, source_helper.project_version,
        self.architecture)


class SetupPyMsiBuildHelper(MsiBuildHelper):
  """Class that helps in building Microsoft Installer packages (.msi)."""

  def _GetFilenameSafeProjectInformation(self, source_helper):
    """Determines the filename safe project name and version.

    Args:
      source_helper: the source helper (instance of SourceHelper).

    Returns:
      A tuple containing the filename safe project name and version.
    """
    if self._dependency_definition.setup_name:
      project_name = self._dependency_definition.setup_name
    else:
      project_name = source_helper.project_name

    if source_helper.project_name == u'dfvfs':
      project_version = u'{0!s}.1'.format(source_helper.project_version)
    else:
      project_version = u'{0!s}'.format(source_helper.project_version)

    return project_name, project_version

  def Build(self, source_helper):
    """Builds the msi.

    Args:
      source_helper: the source helper (instance of SourceHelper).

    Returns:
      True if the build was successful, False otherwise.
    """
    source_filename = source_helper.Download()
    if not source_filename:
      logging.info(u'Download of: {0:s} failed'.format(
          source_helper.project_name))
      return False

    source_directory = source_helper.Create()
    if not source_directory:
      logging.error(
          u'Extraction of source package: {0:s} failed'.format(source_filename))
      return False

    logging.info(u'Building msi of: {0:s}'.format(source_filename))

    command = u'{0:s} setup.py bdist_msi > {1:s} 2>&1'.format(
        sys.executable, os.path.join(u'..', self.LOG_FILENAME))
    exit_code = subprocess.call(
        u'(cd {0:s} && {1:s})'.format(source_directory, command), shell=True)
    if exit_code != 0:
      logging.error(u'Running: "{0:s}" failed.'.format(command))
      return False

    # Move the msi to the build directory.
    project_name, _ = self._GetFilenameSafeProjectInformation(
        source_helper)

    msi_filename = glob.glob(os.path.join(
        source_directory, u'dist', u'{0:s}-*.msi'.format(project_name)))

    logging.info(u'Moving: {0:s}'.format(msi_filename[0]))
    shutil.move(msi_filename[0], '.')

    return True

  def Clean(self, source_helper):
    """Cleans the build and dist directory.

    Args:
      source_helper: the source helper (instance of SourceHelper).
    """
    # Remove previous versions build directories.
    for filename in [u'build', u'dist']:
      if os.path.exists(filename):
        logging.info(u'Removing: {0:s}'.format(filename))
        shutil.rmtree(filename, True)

    # Remove previous versions of MSIs.
    project_name, project_version = self._GetFilenameSafeProjectInformation(
        source_helper)

    if self._dependency_definition.architecture_dependent:
      suffix = u'-py2.7'
    else:
      suffix = u''

    # MSI does not support a single number version therefore we add '.1'.
    if u'.' not in project_version:
      project_version = u'{0!s}.1'.format(project_version)

    filenames_to_ignore = re.compile(u'{0:s}-.*{1!s}.{2:s}{3:s}.msi'.format(
        project_name, project_version, self.architecture, suffix))

    msi_filenames_glob = u'{0:s}-*.{1:s}{2:s}.msi'.format(
        project_name, self.architecture, suffix)

    filenames = glob.glob(msi_filenames_glob)
    for filename in filenames:
      if not filenames_to_ignore.match(filename):
        logging.info(u'Removing: {0:s}'.format(filename))
        os.remove(filename)

  def GetOutputFilename(self, source_helper):
    """Retrieves the filename of one of the resulting files.

    Args:
      source_helper: the source helper (instance of SourceHelper).

    Returns:
      A filename of one of the resulting MSIs.
    """
    project_name, project_version = self._GetFilenameSafeProjectInformation(
        source_helper)

    # TODO: it looks like coverage is no architecture dependent on Windows.
    # Check if it is architecture dependent on other platforms.
    if (self._dependency_definition.architecture_dependent and
        project_name != u'coverage'):
      suffix = u'-py2.7'
    else:
      suffix = u''

    # MSI does not support a single number version therefore we add '.1'.
    if u'.' not in project_version:
      project_version = u'{0!s}.1'.format(project_version)

    return u'{0:s}-{1:s}.{2:s}{3:s}.msi'.format(
        project_name, project_version, self.architecture, suffix)


class PkgBuildHelper(BuildHelper):
  """Class that helps in building MacOS-X packages (.pkg)."""

  def __init__(self, dependency_definition, data_path):
    """Initializes the build helper.

    Args:
      dependency_definition: the dependency definition object (instance of
                             DependencyDefinition).
      data_path: the path to the data directory which contains the patches
                 sub directory.
    """
    super(PkgBuildHelper, self).__init__(dependency_definition, data_path)
    self._pkgbuild = os.path.join(u'/', u'usr', u'bin', u'pkgbuild')

  def _BuildDmg(self, pkg_filename, dmg_filename):
    """Builds the distributable disk image (.dmg) from the pkg.

    Args:
      pkg_filename: the name of the pkg file (which is technically
                    a directory).
      dmg_filename: the name of the dmg file.

    Returns:
      True if the build was successful, False otherwise.
    """
    command = (
        u'hdiutil create {0:s} -srcfolder {1:s} -fs HFS+').format(
            dmg_filename, pkg_filename)
    exit_code = subprocess.call(command, shell=True)
    if exit_code != 0:
      logging.error(u'Running: "{0:s}" failed.'.format(command))
      return False

    return True

  def _BuildPkg(
      self, source_directory, project_identifier, project_version,
      pkg_filename):
    """Builds the distributable disk image (.dmg) from the pkg.

    Args:
      source_directory: the name of the source directory.
      project_identifier: the project identifier.
      project_version: the version of the project.
      pkg_filename: the name of the pkg file (which is technically
                    a directory).

    Returns:
      True if the build was successful, False otherwise.
    """
    command = (
        u'{0:s} --root {1:s}/tmp/ --identifier {2:s} '
        u'--version {3!s} --ownership recommended {4:s}').format(
            self._pkgbuild, source_directory, project_identifier,
            project_version, pkg_filename)
    exit_code = subprocess.call(command, shell=True)
    if exit_code != 0:
      logging.error(u'Running: "{0:s}" failed.'.format(command))
      return False

    return True

  def Clean(self, source_helper):
    """Cleans the MacOS-X packages in the current directory.

    Args:
      source_helper: the source helper (instance of SourceHelper).
    """
    filenames_to_ignore = re.compile(u'^{0:s}-.*{1!s}'.format(
        source_helper.project_name, source_helper.project_version))

    # Remove files of previous versions in the format:
    # project-*version.dmg
    filenames = glob.glob(u'{0:s}-*.dmg'.format(source_helper.project_name))

    for filename in filenames:
      if not filenames_to_ignore.match(filename):
        logging.info(u'Removing: {0:s}'.format(filename))
        os.remove(filename)

    # Remove files of previous versions in the format:
    # project-*version.pkg
    filenames = glob.glob(u'{0:s}-*.pkg'.format(source_helper.project_name))

    for filename in filenames:
      if not filenames_to_ignore.match(filename):
        logging.info(u'Removing: {0:s}'.format(filename))
        os.remove(filename)

  def GetOutputFilename(self, source_helper):
    """Retrieves the filename of one of the resulting files.

    Args:
      source_helper: the source helper (instance of SourceHelper).

    Returns:
      A filename of one of the resulting rpms.
    """
    return u'{0:s}-{1!s}.dmg'.format(
        source_helper.project_name, source_helper.project_version)


class ConfigureMakePkgBuildHelper(PkgBuildHelper):
  """Class that helps in building MacOS-X packages (.pkg)."""

  def Build(self, source_helper):
    """Builds the pkg package and distributable disk image (.dmg).

    Args:
      source_helper: the source helper (instance of SourceHelper).

    Returns:
      True if the build was successful, False otherwise.
    """
    source_filename = source_helper.Download()
    if not source_filename:
      logging.info(u'Download of: {0:s} failed'.format(
          source_helper.project_name))
      return False

    source_directory = source_helper.Create()
    if not source_directory:
      logging.error(
          u'Extraction of source package: {0:s} failed'.format(source_filename))
      return False

    logging.info(u'Building pkg of: {0:s}'.format(source_filename))

    dmg_filename = u'{0:s}-{1!s}.dmg'.format(
        source_helper.project_name, source_helper.project_version)
    pkg_filename = u'{0:s}-{1!s}.pkg'.format(
        source_helper.project_name, source_helper.project_version)
    log_filename = os.path.join(u'..', self.LOG_FILENAME)

    sdks_path = os.path.join(
        u'/', u'Applications', u'Xcode.app', u'Contents', u'Developer',
        u'Platforms', u'MacOSX.platform', u'Developer', u'SDKs')

    for sub_path in [u'MacOSX10.7.sdk', u'MacOSX10.8.sdk', u'MacOSX10.9.sdk']:
      sdk_path = os.path.join(sdks_path, sub_path)
      if os.path.isdir(sub_path):
        break

    if sdk_path:
      cflags = u'CFLAGS="-isysroot {0:s}"'.format(sdk_path)
      ldflags = u'LDFLAGS="-Wl,-syslibroot,{0:s}"'.format(sdk_path)
    else:
      cflags = u''
      ldflags = u''

    if not os.path.exists(pkg_filename):
      if cflags and ldflags:
        command = (
            u'{0:s} {1:s} ./configure --prefix=/usr --enable-python '
            u'--with-pyprefix --disable-dependency-tracking > {2:s} '
            u'2>&1').format(cflags, ldflags, log_filename)
      else:
        command = (
            u'./configure --prefix=/usr --enable-python --with-pyprefix '
            u'> {0:s} 2>&1').format(log_filename)

      exit_code = subprocess.call(
          u'(cd {0:s} && {1:s})'.format(source_directory, command), shell=True)
      if exit_code != 0:
        logging.error(u'Running: "{0:s}" failed.'.format(command))
        return False

      command = u'make >> {0:s} 2>&1'.format(log_filename)
      exit_code = subprocess.call(
          u'(cd {0:s} && {1:s})'.format(source_directory, command), shell=True)
      if exit_code != 0:
        logging.error(u'Running: "{0:s}" failed.'.format(command))
        return False

      command = u'make install DESTDIR={0:s}/tmp >> {1:s} 2>&1'.format(
          os.path.abspath(source_directory), log_filename)
      exit_code = subprocess.call(
          u'(cd {0:s} && {1:s})'.format(source_directory, command), shell=True)
      if exit_code != 0:
        logging.error(u'Running: "{0:s}" failed.'.format(command))
        return False

      share_doc_path = os.path.join(
          source_directory, u'tmp', u'usr', u'share', u'doc',
          source_helper.project_name)
      if not os.path.exists(share_doc_path):
        os.makedirs(share_doc_path)

      shutil.copy(os.path.join(source_directory, u'AUTHORS'), share_doc_path)
      shutil.copy(os.path.join(source_directory, u'COPYING'), share_doc_path)
      shutil.copy(os.path.join(source_directory, u'NEWS'), share_doc_path)
      shutil.copy(os.path.join(source_directory, u'README'), share_doc_path)

      project_identifier = u'com.github.libyal.{0:s}'.format(
          source_helper.project_name)
      if not self._BuildPkg(
          source_directory, project_identifier, source_helper.project_version,
          pkg_filename):
        return False

    if not self._BuildDmg(pkg_filename, dmg_filename):
      return False

    return True


class SetupPyPkgBuildHelper(PkgBuildHelper):
  """Class that helps in building MacOS-X packages (.pkg)."""

  def Build(self, source_helper):
    """Builds the pkg package and distributable disk image (.dmg).

    Args:
      source_helper: the source helper (instance of SourceHelper).

    Returns:
      True if the build was successful, False otherwise.
    """
    source_filename = source_helper.Download()
    if not source_filename:
      logging.info(u'Download of: {0:s} failed'.format(
          source_helper.project_name))
      return False

    source_directory = source_helper.Create()
    if not source_directory:
      logging.error(
          u'Extraction of source package: {0:s} failed'.format(source_filename))
      return False

    logging.info(u'Building pkg of: {0:s}'.format(source_filename))

    dmg_filename = u'{0:s}-{1!s}.dmg'.format(
        source_helper.project_name, source_helper.project_version)
    pkg_filename = u'{0:s}-{1!s}.pkg'.format(
        source_helper.project_name, source_helper.project_version)
    log_filename = os.path.join(u'..', self.LOG_FILENAME)

    if not os.path.exists(pkg_filename):
      command = u'python setup.py build > {0:s} 2>&1'.format(log_filename)
      exit_code = subprocess.call(
          u'(cd {0:s} && {1:s})'.format(source_directory, command), shell=True)
      if exit_code != 0:
        logging.error(u'Running: "{0:s}" failed.'.format(command))
        return False

      command = u'python setup.py install --root={0:s}/tmp > {1:s} 2>&1'.format(
          os.path.abspath(source_directory), log_filename)
      exit_code = subprocess.call(
          u'(cd {0:s} && {1:s})'.format(source_directory, command), shell=True)
      if exit_code != 0:
        logging.error(u'Running: "{0:s}" failed.'.format(command))
        return False

      # Copy the license file to the egg-info sub directory.
      for license_file in [
          u'COPYING', u'LICENSE', u'LICENSE.TXT', u'LICENSE.txt']:
        if not os.path.exists(os.path.join(source_directory, license_file)):
          continue

        command = (
            u'find ./tmp -type d -name \\*.egg-info -exec cp {0:s} {{}} '
            u'\\;').format(license_file)
        exit_code = subprocess.call(
            u'(cd {0:s} && {1:s})'.format(source_directory, command),
            shell=True)
        if exit_code != 0:
          logging.error(u'Running: "{0:s}" failed.'.format(command))
          return False

      project_identifier = source_helper.GetProjectIdentifier()
      if not self._BuildPkg(
          source_directory, project_identifier, source_helper.project_version,
          pkg_filename):
        return False

    if not self._BuildDmg(pkg_filename, dmg_filename):
      return False

    return True


class RpmBuildHelper(BuildHelper):
  """Class that helps in building rpm packages (.rpm)."""

  # TODO: determine BUILD_DEPENDENCIES from the build files?
  _BUILD_DEPENDENCIES = frozenset([
      'git',
      'binutils',
      'autoconf',
      'automake',
      'libtool',
      'gettext-devel',
      'make',
      'pkgconfig',
      'gcc',
      'gcc-c++',
      'flex',
      'byacc',
      'bzip2-devel',
      'openssl-devel',
      'fuse-devel',
      'rpm-build',
      'python-devel',
      'git',
      'python-dateutil',
      'python-setuptools',
      'sqlite-devel',
  ])

  def __init__(self, dependency_definition, data_path):
    """Initializes the build helper.

    Args:
      dependency_definition: the dependency definition object (instance of
                             DependencyDefinition).
      data_path: the path to the data directory which contains the patches
                 sub directory.
    """
    super(RpmBuildHelper, self).__init__(dependency_definition, data_path)
    self.architecture = platform.machine()

    self.rpmbuild_path = os.path.join(u'~', u'rpmbuild')
    self.rpmbuild_path = os.path.expanduser(self.rpmbuild_path)

    self._rpmbuild_rpms_path = os.path.join(
        self.rpmbuild_path, u'RPMS', self.architecture)
    self._rpmbuild_sources_path = os.path.join(self.rpmbuild_path, u'SOURCES')
    self._rpmbuild_specs_path = os.path.join(self.rpmbuild_path, u'SPECS')

  def _BuildFromSpecFile(self, spec_filename):
    """Builds the rpms directly from a spec file.

    Args:
      spec_filename: the name of the spec file as stored in the rpmbuild
                     SPECS sub directory.

    Returns:
      True if the build was successful, False otherwise.
    """
    current_path = os.getcwd()
    os.chdir(self.rpmbuild_path)

    command = u'rpmbuild -ba {0:s} > {1:s} 2>&1'.format(
        os.path.join(u'SPECS', spec_filename), self.LOG_FILENAME)
    exit_code = subprocess.call(command, shell=True)
    if exit_code != 0:
      logging.error(u'Running: "{0:s}" failed.'.format(command))

    os.chdir(current_path)

    return exit_code == 0

  def _BuildFromSourcePackage(self, source_filename):
    """Builds the rpms directly from the source package file.

    For this to work the source package needs to contain a valid rpm .spec file.

    Args:
      source_filename: the name of the source package file.

    Returns:
      True if the build was successful, False otherwise.
    """
    command = u'rpmbuild -ta {0:s} > {1:s} 2>&1'.format(
        source_filename, self.LOG_FILENAME)
    exit_code = subprocess.call(command, shell=True)
    if exit_code != 0:
      logging.error(u'Running: "{0:s}" failed.'.format(command))
      return False

    return True

  def _CreateRpmbuildDirectories(self):
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
      project_name: the name of the project.
      spec_file_data: the spec file data.
    """
    spec_filename = os.path.join(
        self._rpmbuild_specs_path, u'{0:s}.spec'.format(project_name))

    spec_file = open(spec_filename, 'w')
    spec_file.write(spec_file_data)
    spec_file.close()

  def _CopySourceFile(self, source_filename):
    """Copies the source file to the rpmbuild directory.

    Args:
      source_filename: the name of the source package file.
    """
    shutil.copy(source_filename, self._rpmbuild_sources_path)

  def _GetFilenameSafeProjectInformation(self, source_helper):
    """Determines the filename safe project name and version.

    Args:
      source_helper: the source helper (instance of SourceHelper).

    Returns:
      A tuple containing the filename safe project name and version.
    """
    if self._dependency_definition.setup_name:
      project_name = self._dependency_definition.setup_name
    else:
      project_name = source_helper.project_name

    project_version = source_helper.project_version
    if isinstance(project_version, basestring):
      project_version = project_version.replace(u'-', u'_')

    return project_name, project_version

  def _MoveRpms(self, project_name, project_version):
    """Moves the rpms from the rpmbuild directory into to current directory.

    Args:
      project_name: the name of the project.
      project_version: the version of the project.
    """
    filenames = glob.glob(os.path.join(
        self._rpmbuild_rpms_path, u'{0:s}-*{1!s}-1.{2:s}.rpm'.format(
            project_name, project_version, self.architecture)))
    for filename in filenames:
      logging.info(u'Moving: {0:s}'.format(filename))
      shutil.move(filename, u'.')

  @classmethod
  def CheckBuildDependencies(cls):
    """Checks if the build dependencies are met.

    Returns:
      A list of package names that need to be installed or an empty list.
    """
    missing_packages = []
    for package_name in cls._BUILD_DEPENDENCIES:
      if not cls.CheckIsInstalled(package_name):
        missing_packages.append(package_name)

    return missing_packages

  @classmethod
  def CheckIsInstalled(cls, package_name):
    """Checks if a package is installed.

    Args:
      package_name: the name of the package.

    Returns:
      A boolean value containing true if the package is installed
      false otherwise.
    """
    command = u'rpm -qi {0:s} >/dev/null 2>&1'.format(package_name)
    exit_code = subprocess.call(command, shell=True)
    return exit_code == 0

  def Clean(self, source_helper):
    """Cleans the rpmbuild directory.

    Args:
      source_helper: the source helper (instance of SourceHelper).
    """
    project_name, project_version = self._GetFilenameSafeProjectInformation(
        source_helper)

    # Remove previous versions build directories.
    filenames_to_ignore = re.compile(u'{0:s}-{1!s}'.format(
        project_name, project_version))

    filenames = glob.glob(os.path.join(
        self.rpmbuild_path, u'BUILD', u'{0:s}-*'.format(project_name)))
    for filename in filenames:
      if not filenames_to_ignore.match(filename):
        logging.info(u'Removing: {0:s}'.format(filename))
        shutil.rmtree(filename)

    # Remove previous versions of rpms.
    filenames_to_ignore = re.compile(
        u'{0:s}-.*{1!s}-1.{2:s}.rpm'.format(
            project_name, project_version, self.architecture))

    rpm_filenames_glob = u'{0:s}-*-1.{1:s}.rpm'.format(
        project_name, self.architecture)

    filenames = glob.glob(rpm_filenames_glob)
    for filename in filenames:
      if not filenames_to_ignore.match(filename):
        logging.info(u'Removing: {0:s}'.format(filename))
        os.remove(filename)

    filenames = glob.glob(os.path.join(
        self.rpmbuild_path, u'RPMS', self.architecture, rpm_filenames_glob))
    for filename in filenames:
      if not filenames_to_ignore.match(filename):
        logging.info(u'Removing: {0:s}'.format(filename))
        os.remove(filename)

    # Remove previous versions of source rpms.
    filenames_to_ignore = re.compile(u'{0:s}-.*{1!s}-1.src.rpm'.format(
        project_name, project_version))

    filenames = glob.glob(os.path.join(
        self.rpmbuild_path, u'SRPMS',
        u'{0:s}-*-1.src.rpm'.format(project_name)))
    for filename in filenames:
      if not filenames_to_ignore.match(filename):
        logging.info(u'Removing: {0:s}'.format(filename))
        os.remove(filename)

  def GetOutputFilename(self, source_helper):
    """Retrieves the filename of one of the resulting files.

    Args:
      source_helper: the source helper (instance of SourceHelper).

    Returns:
      A filename of one of the resulting rpms.
    """
    project_name, project_version = self._GetFilenameSafeProjectInformation(
        source_helper)

    return u'{0:s}-{1!s}-1.{2:s}.rpm'.format(
        project_name, project_version, self.architecture)


class ConfigureMakeRpmBuildHelper(RpmBuildHelper):
  """Class that helps in building rpm packages (.rpm)."""

  def Build(self, source_helper):
    """Builds the rpms.

    Args:
      source_helper: the source helper (instance of SourceHelper).

    Returns:
      True if the build was successful, False otherwise.
    """
    source_filename = source_helper.Download()
    if not source_filename:
      logging.info(u'Download of: {0:s} failed'.format(
          source_helper.project_name))
      return False

    logging.info(u'Building rpm of: {0:s}'.format(source_filename))

    project_name, project_version = self._GetFilenameSafeProjectInformation(
        source_helper)

    # rpmbuild wants the project filename without the status indication.
    rpm_source_filename = u'{0:s}-{1!s}.tar.gz'.format(
        project_name, project_version)
    os.rename(source_filename, rpm_source_filename)

    build_successful = self._BuildFromSourcePackage(rpm_source_filename)

    if build_successful:
      # Move the rpms to the build directory.
      self._MoveRpms(project_name, project_version)

      # Remove BUILD directory.
      filename = os.path.join(
          self.rpmbuild_path, u'BUILD', u'{0:s}-{1!s}'.format(
              project_name, project_version))
      logging.info(u'Removing: {0:s}'.format(filename))
      shutil.rmtree(filename)

      # Remove SRPMS file.
      filename = os.path.join(
          self.rpmbuild_path, u'SRPMS', u'{0:s}-{1!s}-1.src.rpm'.format(
              project_name, project_version))
      logging.info(u'Removing: {0:s}'.format(filename))
      os.remove(filename)

    # Change the project filename back to the original.
    os.rename(rpm_source_filename, source_filename)

    return build_successful


class SetupPyRpmBuildHelper(RpmBuildHelper):
  """Class that helps in building rpm packages (.rpm)."""

  def __init__(self, dependency_definition, data_path):
    """Initializes the build helper.

    Args:
      dependency_definition: the dependency definition object (instance of
                             DependencyDefinition).
      data_path: the path to the data directory which contains the patches
                 sub directory.
    """
    super(SetupPyRpmBuildHelper, self).__init__(
        dependency_definition, data_path)
    if not dependency_definition.architecture_dependent:
      self.architecture = 'noarch'

  def Build(self, source_helper):
    """Builds the rpms.

    Args:
      source_helper: the source helper (instance of SourceHelper).

    Returns:
      True if the build was successful, False otherwise.
    """
    source_filename = source_helper.Download()
    if not source_filename:
      logging.info(u'Download of: {0:s} failed'.format(
          source_helper.project_name))
      return False

    logging.info(u'Building rpm of: {0:s}'.format(source_filename))

    source_directory = source_helper.Create()
    if not source_directory:
      logging.error(
          u'Extraction of source package: {0:s} failed'.format(source_filename))
      return False

    command = u'python setup.py bdist_rpm > {0:s} 2>&1'.format(
        os.path.join(u'..', self.LOG_FILENAME))
    exit_code = subprocess.call(
        u'(cd {0:s} && {1:s})'.format(source_directory, command), shell=True)
    if exit_code != 0:
      logging.error(u'Running: "{0:s}" failed.'.format(command))
      return False

    # Move the rpms to the build directory.
    project_name, project_version = self._GetFilenameSafeProjectInformation(
        source_helper)

    filenames = glob.glob(os.path.join(
        source_directory, u'dist', u'{0:s}-{1!s}-1.{2:s}.rpm'.format(
            project_name, project_version, self.architecture)))
    for filename in filenames:
      logging.info(u'Moving: {0:s}'.format(filename))
      shutil.move(filename, '.')

    return True

  def Clean(self, source_helper):
    """Cleans the build and dist directory.

    Args:
      source_helper: the source helper (instance of SourceHelper).
    """
    # Remove previous versions build directories.
    for filename in [u'build', u'dist']:
      if os.path.exists(filename):
        logging.info(u'Removing: {0:s}'.format(filename))
        shutil.rmtree(filename, True)

    # Remove previous versions of rpms.
    project_name, project_version = self._GetFilenameSafeProjectInformation(
        source_helper)

    filenames_to_ignore = re.compile(u'{0:s}-.*{1!s}-1.{2:s}.rpm'.format(
        project_name, project_version, self.architecture))

    rpm_filenames_glob = u'{0:s}-*-1.{1:s}.rpm'.format(
        project_name, self.architecture)

    filenames = glob.glob(rpm_filenames_glob)
    for filename in filenames:
      if not filenames_to_ignore.match(filename):
        logging.info(u'Removing: {0:s}'.format(filename))
        os.remove(filename)
