#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Script to automate creating builds of projects."""

import argparse
import logging
import os
import subprocess
import sys

try:
  import ConfigParser as configparser
except ImportError:
  import configparser

from l2tdevtools import build_helper
from l2tdevtools import download_helper
from l2tdevtools import source_helper


# Since os.path.abspath() uses the current working directory (cwd)
# os.path.abspath(__file__) will point to a different location if
# cwd has been changed. Hence we preserve the absolute location of __file__.
__file__ = os.path.abspath(__file__)


# TODO: look into merging functionality with update dependencies script.


class DependencyDefinition(object):
  """Class that implements a dependency definition."""

  def __init__(self, name):
    """Initializes the dependency definition.

    Args:
      name: the name of the dependency.
    """
    self.architecture_dependent = False
    self.description_long = None
    self.description_short = None
    self.disabled = False
    self.dpkg_dependencies = None
    self.dpkg_name = None
    self.download_url = None
    self.homepage_url = None
    self.maintainer = None
    self.name = name
    self.setup_name = None


class DependencyDefinitionReader(object):
  """Class that implements a dependency definition reader."""

  def _GetConfigValue(self, config_parser, section_name, value_name):
    """Retrieves a value from the config parser.

    Args:
      config_parser: the configuration parser (instance of ConfigParser).
      section_name: the name of the section that contains the value.
      value_name: the name of the value.

    Returns:
      An object containing the value or None if the value does not exists.
    """
    try:
      return config_parser.get(section_name, value_name).decode('utf-8')
    except configparser.NoOptionError:
      return

  def Read(self, file_object):
    """Reads dependency definitions.

    Args:
      file_object: the file-like object to read from.

    Yields:
      Dependency definitions (instances of DependencyDefinition).
    """
    # TODO: replace by:
    # config_parser = configparser. ConfigParser(interpolation=None)
    config_parser = configparser.RawConfigParser()
    config_parser.readfp(file_object)

    for section_name in config_parser.sections():
      dependency_definition = DependencyDefinition(section_name)

      dependency_definition.architecture_dependent = self._GetConfigValue(
          config_parser, section_name, u'architecture_dependent')
      dependency_definition.description_long = self._GetConfigValue(
          config_parser, section_name, u'description_long')
      dependency_definition.description_short = self._GetConfigValue(
          config_parser, section_name, u'description_short')
      dependency_definition.disabled = self._GetConfigValue(
          config_parser, section_name, u'disabled')
      dependency_definition.dpkg_dependencies = self._GetConfigValue(
          config_parser, section_name, u'dpkg_dependencies')
      dependency_definition.dpkg_name = self._GetConfigValue(
          config_parser, section_name, u'dpkg_name')
      dependency_definition.download_url = self._GetConfigValue(
          config_parser, section_name, u'download_url')
      dependency_definition.homepage_url = self._GetConfigValue(
          config_parser, section_name, u'homepage_url')
      dependency_definition.maintainer = self._GetConfigValue(
          config_parser, section_name, u'maintainer')
      dependency_definition.setup_name = self._GetConfigValue(
          config_parser, section_name, u'setup_name')

      # Need at minimum a name and a download URL.
      if dependency_definition.name and dependency_definition.download_url:
        yield dependency_definition


class DependencyBuilder(object):
  """Class that helps in building dependencies."""

  # TODO: add phases for building sleuthkit/pytsk.

  # The distributions to build dpkg-source packages for.
  _DPKG_SOURCE_DISTRIBUTIONS = frozenset([u'precise', u'trusty'])

  _LIBYAL_LIBRARIES = frozenset([u'libewf'])

  _PATCHES_URL = (
      u'https://googledrive.com/host/0B30H7z4S52FleW5vUHBnblJfcjg/'
      u'3rd%20party/patches')

  _PYTHON_MODULES = frozenset([
      u'binplist', u'dateutil', u'docopt', u'dfvfs', u'dpkt', u'pefile',
      u'pyparsing'])

  def __init__(self, build_target):
    """Initializes the dependency builder.

    Args:
      build_target: the build target.
    """
    super(DependencyBuilder, self).__init__()
    self._build_target = build_target

  def _BuildDependency(self, download_helper_object, dependency_definition):
    """Builds a dependency.

    Args:
      download_helper_object: the download helper (instance of DownloadHelper).
      dependency_definition: the dependency definition object (instance of
                             DependencyDefinition).

    Returns:
      True if the build is successful or False on error.
    """
    source_helper_object = source_helper.SourcePackageHelper(
        download_helper_object, dependency_definition.name)

    source_helper_object.Clean()

    # Unify http:// and https:// URLs for the download helper check.
    download_url = dependency_definition.download_url
    if download_url.startswith(u'https://'):
      download_url = u'http://{0:s}'.format(download_url[8:])

    if self._build_target == u'download':
      source_filename = source_helper_object.Download()

      # If available run the script post-download.sh after download.
      if os.path.exists(u'post-download.sh'):
        command = u'sh ./post-download.sh {0:s}'.format(source_filename)
        exit_code = subprocess.call(command, shell=True)
        if exit_code != 0:
          logging.error(u'Running: "{0:s}" failed.'.format(command))
          return False

    elif (dependency_definition.name in self._LIBYAL_LIBRARIES or
          download_url.startswith(u'http://github.com/libyal/')):
      if not self._BuildLibyalLibrary(
          source_helper_object, dependency_definition):
        return False

    elif (dependency_definition.name in self._PYTHON_MODULES or
          download_url.startswith(u'http://pypi.python.org/pypi/')):
      if not self._BuildPythonModule(
          source_helper_object, dependency_definition):
        return False

    else:
      logging.warning(u'Unable to determine how to build: {0:s}'.format(
          dependency_definition.name))
      return False

    return True

  def _BuildLibyalLibrary(self, source_helper_object, dependency_definition):
    """Builds a libyal project and its Python module dependency.

    Args:
      source_helper_object: the source helper (instance of SourceHelper).
      dependency_definition: the dependency definition object (instance of
                             DependencyDefinition).

    Returns:
      True if the build is successful or False on error.
    """
    build_helper_object = None
    distributions = [None]
    if self._build_target == u'dpkg':
      build_helper_object = build_helper.LibyalDpkgBuildHelper(
          dependency_definition)

    elif self._build_target == u'dpkg-source':
      build_helper_object = build_helper.LibyalSourceDpkgBuildHelper(
          dependency_definition)
      distributions = self._DPKG_SOURCE_DISTRIBUTIONS

    elif self._build_target == u'msi':
      # TODO: setup dokan and zlib in build directory.
      build_helper_object = build_helper.LibyalMsiBuildHelper(
          dependency_definition)

    elif self._build_target == u'pkg':
      build_helper_object = build_helper.LibyalPkgBuildHelper(
          dependency_definition)

    elif self._build_target == u'rpm':
      build_helper_object = build_helper.LibyalRpmBuildHelper(
          dependency_definition)

    if not build_helper_object:
      return False

    for distribution in distributions:
      if distribution:
        build_helper_object.distribution = distribution

      output_filename = build_helper_object.GetOutputFilename(
          source_helper_object)

      build_helper_object.Clean(source_helper_object)

      if not os.path.exists(output_filename):
        if not build_helper_object.Build(source_helper_object):
          logging.warning((
              u'Build of: {0:s} failed, for more information check '
              u'{1:s}').format(
                  source_helper_object.project_name,
                  build_helper_object.LOG_FILENAME))
          return False

      if os.path.exists(build_helper_object.LOG_FILENAME):
        logging.info(u'Removing: {0:s}'.format(
            build_helper_object.LOG_FILENAME))
        os.remove(build_helper_object.LOG_FILENAME)

    return True

  def _BuildPythonModule(self, source_helper_object, dependency_definition):
    """Builds a Python module dependency.

    Args:
      source_helper_object: the source helper (instance of SourceHelper).
      dependency_definition: the dependency definition object (instance of
                             DependencyDefinition).

    Returns:
      True if the build is successful or False on error.
    """
    build_helper_object = None
    distributions = [None]
    if self._build_target == u'dpkg':
      build_helper_object = build_helper.PythonModuleDpkgBuildHelper(
          dependency_definition)

    elif self._build_target == u'dpkg-source':
      build_helper_object = build_helper.PythonModuleSourceDpkgBuildHelper(
          dependency_definition)
      distributions = self._DPKG_SOURCE_DISTRIBUTIONS

    elif self._build_target == u'msi':
      # TODO: setup sqlite in build directory.
      build_helper_object = build_helper.PythonModuleMsiBuildHelper(
          dependency_definition)

    elif self._build_target == u'pkg':
      build_helper_object = build_helper.PythonModulePkgBuildHelper(
          dependency_definition)

    elif self._build_target == u'rpm':
      build_helper_object = build_helper.PythonModuleRpmBuildHelper(
          dependency_definition)

    if not build_helper_object:
      return False

    for distribution in distributions:
      if distribution:
        build_helper_object.distribution = distribution

      output_filename = build_helper_object.GetOutputFilename(
          source_helper_object)

      build_helper_object.Clean(source_helper_object)

      if not os.path.exists(output_filename):
        if not build_helper_object.Build(source_helper_object):
          logging.warning((
              u'Build of: {0:s} failed, for more information check '
              u'{1:s}').format(
                  source_helper_object.project_name,
                  build_helper_object.LOG_FILENAME))
          return False

      if os.path.exists(build_helper_object.LOG_FILENAME):
        logging.info(u'Removing: {0:s}'.format(
            build_helper_object.LOG_FILENAME))
        os.remove(build_helper_object.LOG_FILENAME)

    return True

  def Build(self, dependency_definition):
    """Builds a dependency.

    Args:
      dependency_definition: the dependency definition object (instance of
                             DependencyDefinition).

    Returns:
      True if the build is successful or False on error.

    Raises:
      ValueError: if the project type is unsupported.
    """
    download_url = dependency_definition.download_url
    if download_url.endswith(u'/'):
      download_url = download_url[:-1]

    # Unify http:// and https:// URLs for the download helper check.
    if download_url.startswith(u'https://'):
      download_url = u'http://{0:s}'.format(download_url[8:])

    if (download_url.startswith(u'http://code.google.com/p/') and
        download_url.endswith(u'/downloads/list')):
      download_helper_object = download_helper.GoogleCodeWikiDownloadHelper()

    elif download_url.startswith(u'http://pypi.python.org/pypi/'):
      download_helper_object = download_helper.PyPiDownloadHelper()

    elif (download_url.startswith(u'http://sourceforge.net/projects/') and
          download_url.endswith(u'/files')):
      download_helper_object = download_helper.SourceForgeDownloadHelper()

    # TODO: make this a more generic github download helper when
    # when Google Drive support is no longer needed.
    elif (download_url.startswith(u'http://github.com/libyal/') or
          download_url.startswith(u'http://googledrive.com/host/')):
      download_helper_object = download_helper.LibyalGitHubDownloadHelper()

    elif (download_url.startswith(u'http://github.com/') and
          download_url.endswith(u'/releases')):
      organization, _, _ = download_url[18:-9].rpartition(u'/')
      download_helper_object = (
          download_helper.GithubReleasesDownloadHelper(organization))

    else:
      raise ValueError(u'Unsupported download URL: {0:s}.'.format(download_url))

    return self._BuildDependency(download_helper_object, dependency_definition)


def Main():
  build_targets = frozenset([
      u'download', u'dpkg', u'dpkg-source', u'msi', u'pkg', u'rpm'])

  args_parser = argparse.ArgumentParser(description=(
      u'Downloads and builds the latest versions of projects.'))

  args_parser.add_argument(
      u'build_target', choices=sorted(build_targets), action=u'store',
      metavar=u'BUILD_TARGET', default=None, help=u'The build target.')

  args_parser.add_argument(
      u'--build-directory', u'--build_directory', action=u'store',
      metavar=u'DIRECTORY', dest=u'build_directory', type=unicode,
      default=u'build', help=u'The location of the the build directory.')

  args_parser.add_argument(
      u'-c', u'--config', dest=u'config_file', action=u'store',
      metavar=u'CONFIG_FILE', default=None,
      help=u'path of the build configuration file.')

  options = args_parser.parse_args()

  if not options.build_target:
    print u'Build target missing.'
    print u''
    args_parser.print_help()
    print u''
    return False

  if options.build_target not in build_targets:
    print u'Unsupported build target: {0:s}.'.format(options.build_target)
    print u''
    args_parser.print_help()
    print u''
    return False

  if not options.config_file:
    options.config_file = os.path.dirname(__file__)
    options.config_file = os.path.dirname(options.config_file)
    options.config_file = os.path.join(
        options.config_file, u'data', u'projects.ini')

  if not os.path.exists(options.config_file):
    print u'No such config file: {0:s}.'.format(options.config_file)
    print u''
    return False

  logging.basicConfig(
      level=logging.INFO, format=u'[%(levelname)s] %(message)s')

  if options.build_target in [u'dpkg', u'dpkg-source']:
    missing_packages = build_helper.DpkgBuildHelper.CheckBuildDependencies()
    if missing_packages:
      print (u'Required build package(s) missing. Please install: '
             u'{0:s}.'.format(u', '.join(missing_packages)))
      print u''
      return False

  elif options.build_target == u'rpm':
    missing_packages = build_helper.RpmBuildHelper.CheckBuildDependencies()
    if missing_packages:
      print (u'Required build package(s) missing. Please install: '
             u'{0:s}.'.format(u', '.join(missing_packages)))
      print u''
      return False

  dependency_builder = DependencyBuilder(options.build_target)

  # TODO: allow for patching e.g. dpkt 1.8.
  # Have builder check patches URL.

  # TODO: package ipython.

  # TODO:
  # (u'protobuf', DependencyBuilder.PROJECT_TYPE_GOOGLE_CODE_WIKI),
  # ./configure
  # make
  # cd python
  # python setup.py build
  # python setup.py install --root $PWD/tmp
  #
  # Build of rpm fails:
  # python setup.py bdist_rpm
  #
  # Solution: use protobuf-python.spec to build

  # TODO: download and build sqlite3 from source?
  # http://www.sqlite.org/download.html
  # or copy sqlite3.h, .lib and .dll to src/ directory?

  # TODO: rpm build of psutil is broken, fix upstream or add patching.
  # (u'psutil', DependencyBuilder.PROJECT_TYPE_PYPI),

  builds = []
  with open(options.config_file) as file_object:
    dependency_definition_reader = DependencyDefinitionReader()
    for dependency_definition in dependency_definition_reader.Read(file_object):
      if not dependency_definition.disabled:
        builds.append(dependency_definition)

  if not os.path.exists(options.build_directory):
    os.mkdir(options.build_directory)

  current_working_directory = os.getcwd()
  os.chdir(options.build_directory)

  result = True
  for dependency_definition in builds:
    logging.info(u'Processing: {0:s}'.format(dependency_definition.name))
    if not dependency_builder.Build(dependency_definition):
      print u'Failed building: {0:s}'.format(dependency_definition.name)
      result = False
      break

  os.chdir(current_working_directory)

  return result


if __name__ == '__main__':
  if not Main():
    sys.exit(1)
  else:
    sys.exit(0)
