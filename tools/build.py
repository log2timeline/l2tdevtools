#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Script to automate creating builds of projects."""

from __future__ import print_function
import argparse
import logging
import os
import subprocess
import sys

from l2tdevtools import build_helper
from l2tdevtools import dependencies
from l2tdevtools import download_helper
from l2tdevtools import source_helper


# Since os.path.abspath() uses the current working directory (cwd)
# os.path.abspath(__file__) will point to a different location if
# cwd has been changed. Hence we preserve the absolute location of __file__.
__file__ = os.path.abspath(__file__)


# TODO: look into merging functionality with update dependencies script.


class DependencyBuilder(object):
  """Class that helps in building dependencies."""

  # TODO: add phases for building sleuthkit/pytsk.

  # The distributions to build dpkg-source packages for.
  _DPKG_SOURCE_DISTRIBUTIONS = frozenset([
      u'precise', u'trusty', u'utopic', u'vivid', u'wily'])

  _LIBYAL_LIBRARIES = frozenset([u'libewf'])

  _PATCHES_URL = (
      u'https://googledrive.com/host/0B30H7z4S52FleW5vUHBnblJfcjg/'
      u'3rd%20party/patches')

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

    elif dependency_definition.build_system == u'configure_make':
      if not self._BuildConfigureMake(
          source_helper_object, dependency_definition):
        return False

    elif dependency_definition.build_system == u'setup_py':
      if not self._BuildSetupPy(
          source_helper_object, dependency_definition):
        return False

    else:
      logging.warning(u'Unable to determine how to build: {0:s}'.format(
          dependency_definition.name))
      return False

    return True

  def _BuildConfigureMake(self, source_helper_object, dependency_definition):
    """Builds a Python module that comes with configure and make.

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
      build_helper_object = build_helper.ConfigureMakeDpkgBuildHelper(
          dependency_definition)

    elif self._build_target == u'dpkg-source':
      build_helper_object = build_helper.ConfigureMakeSourceDpkgBuildHelper(
          dependency_definition)
      distributions = self._DPKG_SOURCE_DISTRIBUTIONS

    elif self._build_target == u'msi':
      build_helper_object = build_helper.ConfigureMakeMsiBuildHelper(
          dependency_definition, os.path.dirname(__file__))

    elif self._build_target == u'pkg':
      build_helper_object = build_helper.ConfigureMakePkgBuildHelper(
          dependency_definition)

    elif self._build_target == u'rpm':
      build_helper_object = build_helper.ConfigureMakeRpmBuildHelper(
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
          if not os.path.exists(build_helper_object.LOG_FILENAME):
            logging.warning(u'Build of: {0:s} failed.'.format(
                source_helper_object.project_name))
          else:
            log_filename = u'{0:s}_{1:s}'.format(
                source_helper_object.project_name,
                build_helper_object.LOG_FILENAME)

            # Remove older logfiles if they exists otherwise the rename
            # fails on Windows.
            if os.path.exists(log_filename):
              os.remove(log_filename)

            os.rename(build_helper_object.LOG_FILENAME, log_filename)
            logging.warning((
                u'Build of: {0:s} failed, for more information check '
                u'{1:s}').format(
                    source_helper_object.project_name, log_filename))
          return False

      if os.path.exists(build_helper_object.LOG_FILENAME):
        logging.info(u'Removing: {0:s}'.format(
            build_helper_object.LOG_FILENAME))
        os.remove(build_helper_object.LOG_FILENAME)

    return True

  def _BuildSetupPy(self, source_helper_object, dependency_definition):
    """Builds a Python module that comes with setup.py.

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
      build_helper_object = build_helper.SetupPyDpkgBuildHelper(
          dependency_definition)

    elif self._build_target == u'dpkg-source':
      build_helper_object = build_helper.SetupPySourceDpkgBuildHelper(
          dependency_definition)
      distributions = self._DPKG_SOURCE_DISTRIBUTIONS

    elif self._build_target == u'msi':
      # TODO: setup sqlite in build directory.
      build_helper_object = build_helper.SetupPyMsiBuildHelper(
          dependency_definition)

    elif self._build_target == u'pkg':
      build_helper_object = build_helper.SetupPyPkgBuildHelper(
          dependency_definition)

    elif self._build_target == u'rpm':
      build_helper_object = build_helper.SetupPyRpmBuildHelper(
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
          if not os.path.exists(build_helper_object.LOG_FILENAME):
            logging.warning(u'Build of: {0:s} failed.'.format(
                source_helper_object.project_name))
          else:
            log_filename = u'{0:s}_{1:s}'.format(
                source_helper_object.project_name,
                build_helper_object.LOG_FILENAME)

            # Remove older logfiles if they exists otherwise the rename
            # fails on Windows.
            if os.path.exists(log_filename):
              os.remove(log_filename)

            os.rename(build_helper_object.LOG_FILENAME, log_filename)
            logging.warning((
                u'Build of: {0:s} failed, for more information check '
                u'{1:s}').format(
                    source_helper_object.project_name, log_filename))
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

  argument_parser = argparse.ArgumentParser(description=(
      u'Downloads and builds the latest versions of projects.'))

  argument_parser.add_argument(
      u'build_target', choices=sorted(build_targets), action=u'store',
      metavar=u'BUILD_TARGET', default=None, help=u'The build target.')

  argument_parser.add_argument(
      u'--build-directory', u'--build_directory', action=u'store',
      metavar=u'DIRECTORY', dest=u'build_directory', type=unicode,
      default=u'build', help=u'The location of the the build directory.')

  argument_parser.add_argument(
      u'-c', u'--config', dest=u'config_file', action=u'store',
      metavar=u'CONFIG_FILE', default=None,
      help=u'path of the build configuration file.')

  argument_parser.add_argument(
      u'--projects', dest=u'projects', action=u'store',
      metavar=u'PROJECT_NAME(S)', default=None,
      help=(
          u'comma separated list of specific project names to build. The '
          u'default is to build all project defined in the configuration '
          u'file.'))

  options = argument_parser.parse_args()

  if not options.build_target:
    print(u'Build target missing.')
    print(u'')
    argument_parser.print_help()
    print(u'')
    return False

  if options.build_target not in build_targets:
    print(u'Unsupported build target: {0:s}.'.format(options.build_target))
    print(u'')
    argument_parser.print_help()
    print(u'')
    return False

  if not options.config_file:
    options.config_file = os.path.dirname(__file__)
    options.config_file = os.path.dirname(options.config_file)
    options.config_file = os.path.join(
        options.config_file, u'data', u'projects.ini')

  if not os.path.exists(options.config_file):
    print(u'No such config file: {0:s}.'.format(options.config_file))
    print(u'')
    return False

  logging.basicConfig(
      level=logging.INFO, format=u'[%(levelname)s] %(message)s')

  if options.projects:
    projects = options.projects.split(u',')
  else:
    projects = []

  if options.build_target in [u'dpkg', u'dpkg-source']:
    missing_packages = build_helper.DpkgBuildHelper.CheckBuildDependencies()
    if missing_packages:
      print((u'Required build package(s) missing. Please install: '
             u'{0:s}.'.format(u', '.join(missing_packages))))
      print(u'')
      return False

  elif options.build_target == u'msi':
    zlib_dependent_projects = frozenset([u'libewf', u'libqcow', u'libvmdk'])
    if set(projects).intersection(zlib_dependent_projects):
      download_helper_object = download_helper.SourceForgeDownloadHelper()
      source_helper_object = source_helper.SourcePackageHelper(
          download_helper_object, u'zlib')

      source_filename = source_helper_object.Download()
      if not source_filename:
        logging.info(u'Download of: {0:s} failed'.format(
            source_helper_object.project_name))
        return False

      source_directory = source_helper_object.Create()
      if not source_directory:
        logging.error(
            u'Extraction of source package: {0:s} failed'.format(
                source_filename))
        return False

    # TODO: setup dokan in build directory.

  elif options.build_target == u'rpm':
    missing_packages = build_helper.RpmBuildHelper.CheckBuildDependencies()
    if missing_packages:
      print((u'Required build package(s) missing. Please install: '
             u'{0:s}.'.format(u', '.join(missing_packages))))
      print(u'')
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
    dependency_definition_reader = dependencies.DependencyDefinitionReader()
    for dependency_definition in dependency_definition_reader.Read(file_object):
      is_disabled = False
      if (options.build_target in dependency_definition.disabled or
          u'all' in dependency_definition.disabled):
        if dependency_definition.name not in projects:
          is_disabled = True
        else:
          # If a project is manually specified ignore the disabled status.
          logging.info(u'Ignoring disabled status for: {0:s}'.format(
              dependency_definition.name))

      if not is_disabled:
        builds.append(dependency_definition)

  if not os.path.exists(options.build_directory):
    os.mkdir(options.build_directory)

  current_working_directory = os.getcwd()
  os.chdir(options.build_directory)

  failed_builds = []
  for dependency_definition in builds:
    if dependency_definition.name not in projects:
      continue

    logging.info(u'Processing: {0:s}'.format(dependency_definition.name))
    if not dependency_builder.Build(dependency_definition):
      print(u'Failed building: {0:s}'.format(dependency_definition.name))
      failed_builds.append(dependency_definition.name)

  os.chdir(current_working_directory)

  if failed_builds:
    print(u'')
    print(u'Failed buiding:')
    for failed_build in failed_builds:
      print(u'\t{0:s}'.format(failed_build))

  return not failed_builds


if __name__ == '__main__':
  if not Main():
    sys.exit(1)
  else:
    sys.exit(0)
