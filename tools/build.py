#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Script to automate creating builds of projects."""

from __future__ import print_function
from __future__ import unicode_literals

import argparse
import io
import logging
import os
import subprocess
import sys

from l2tdevtools import build_helper
from l2tdevtools import download_helper
from l2tdevtools import presets
from l2tdevtools import projects
from l2tdevtools import source_helper


# Since os.path.abspath() uses the current working directory (cwd)
# os.path.abspath(__file__) will point to a different location if
# cwd has been changed. Hence we preserve the absolute location of __file__.
__file__ = os.path.abspath(__file__)


# TODO: look into merging functionality with update script.

class ProjectBuilder(object):
  """Class that helps in building projects."""

  # The distributions to build dpkg-source packages for.
  _DPKG_SOURCE_DISTRIBUTIONS = frozenset([
      'trusty', 'xenial', 'bionic'])

  def __init__(self, build_target):
    """Initializes the project builder.

    Args:
      build_target (str): build target.
    """
    super(ProjectBuilder, self).__init__()
    self._build_target = build_target
    self._l2tdevtools_path = os.path.dirname(os.path.dirname(__file__))

  def _BuildProject(self, download_helper_object, project_definition):
    """Builds a project.

    Args:
      download_helper_object (DownloadHelper): download helper.
      project_definition (ProjectDefinition): project definition.

    Returns:
      bool: True if the build is successful or False on error.
    """
    project_name = project_definition.name

    source_helper_object = source_helper.SourcePackageHelper(
        project_name, project_definition, download_helper_object)

    source_helper_object.Clean()

    # TODO: add a step to make sure build environment is sane
    # e.g. _CheckStatusIsClean()

    # Unify http:// and https:// URLs for the download helper check.
    download_url = project_definition.download_url
    if download_url.startswith('https://'):
      download_url = 'http://{0:s}'.format(download_url[8:])

    if self._build_target == 'download':
      source_filename = source_helper_object.Download()

      # If available run the script post-download.sh after download.
      if os.path.exists('post-download.sh'):
        command = 'sh ./post-download.sh {0:s}'.format(source_filename)
        exit_code = subprocess.call(command, shell=True)
        if exit_code != 0:
          logging.error('Running: "{0:s}" failed.'.format(command))
          return False

      return True

    build_helper_object = build_helper.BuildHelperFactory.NewBuildHelper(
        project_definition, self._build_target, self._l2tdevtools_path)
    if not build_helper_object:
      logging.warning('Unable to determine how to build: {0:s}'.format(
          project_definition.name))
      return False

    build_dependencies = build_helper_object.CheckBuildDependencies()
    if build_dependencies:
      logging.warning(
          'Missing build dependencies: {0:s}'.format(
              ' '.join(build_dependencies)))
      return False

    if self._build_target == 'dpkg-source':
      distributions = self._DPKG_SOURCE_DISTRIBUTIONS
    else:
      distributions = [None]

    for distribution in distributions:
      if not self._BuildProjectForDistribution(
          build_helper_object, source_helper_object, distribution):
        return False

    if os.path.exists(build_helper_object.LOG_FILENAME):
      logging.info('Removing: {0:s}'.format(
          build_helper_object.LOG_FILENAME))
      os.remove(build_helper_object.LOG_FILENAME)

    return True

  def _BuildProjectForDistribution(
      self, build_helper_object, source_helper_object, distribution):
    """Builds a project for a specific distribution.

    Args:
      build_helper_object (BuildHelper): build helper.
      source_helper_object (SourceHelper): source helper.
      distribution (str): name of the distribution.

    Returns:
      bool: True if the build is successful or False on error.
    """
    if distribution:
      build_helper_object.distribution = distribution

    build_required = build_helper_object.CheckBuildRequired(
        source_helper_object)

    build_helper_object.Clean(source_helper_object)

    if not build_required or build_helper_object.Build(source_helper_object):
      return True

    if not os.path.exists(build_helper_object.LOG_FILENAME):
      logging.warning('Build of: {0:s} failed.'.format(
          source_helper_object.project_name))
    else:
      log_filename = '{0:s}_{1:s}'.format(
          source_helper_object.project_name,
          build_helper_object.LOG_FILENAME)

      # Remove older logfiles if they exists otherwise the rename
      # fails on Windows.
      if os.path.exists(log_filename):
        os.remove(log_filename)

      os.rename(build_helper_object.LOG_FILENAME, log_filename)
      logging.warning((
          'Build of: {0:s} failed, for more information check '
          '{1:s}').format(
              source_helper_object.project_name, log_filename))

    return False

  def Build(self, project_definition):
    """Builds a project.

    Args:
      project_definition (ProjectDefinition): project definition.

    Returns:
      bool: True if the build is successful or False on error.

    Raises:
      ValueError: if the project type is unsupported.
    """
    download_helper_object = (
        download_helper.DownloadHelperFactory.NewDownloadHelper(
            project_definition.download_url))

    if not download_helper_object:
      raise ValueError('Unsupported download URL: {0:s}.'.format(
          project_definition.download_url))

    return self._BuildProject(download_helper_object, project_definition)


def Main():
  """The main program function.

  Returns:
    bool: True if successful or False if not.
  """
  build_targets = frozenset([
      'download', 'dpkg', 'dpkg-source', 'msi', 'osc', 'pkg',
      'rpm', 'source', 'srpm'])

  argument_parser = argparse.ArgumentParser(description=(
      'Downloads and builds the latest versions of projects.'))

  argument_parser.add_argument(
      'build_target', choices=sorted(build_targets), action='store',
      metavar='BUILD_TARGET', default=None, help='The build target.')

  argument_parser.add_argument(
      '--build-directory', '--build_directory', action='store',
      metavar='DIRECTORY', dest='build_directory', type=str,
      default='build', help='The location of the build directory.')

  argument_parser.add_argument(
      '-c', '--config', dest='config_path', action='store',
      metavar='CONFIG_PATH', default=None, help=(
          'path of the directory containing the build configuration '
          'files e.g. projects.ini.'))

  argument_parser.add_argument(
      '--preset', dest='preset', action='store',
      metavar='PRESET_NAME', default=None, help=(
          'name of the preset of project names to build. The default is to '
          'build all project defined in the projects.ini configuration file. '
          'The presets are defined in the preset.ini configuration file.'))

  argument_parser.add_argument(
      '--projects', dest='projects', action='store',
      metavar='PROJECT_NAME(S)', default=None, help=(
          'comma separated list of specific project names to build. The '
          'default is to build all project defined in the projects.ini '
          'configuration file.'))

  options = argument_parser.parse_args()

  if not options.build_target:
    print('Build target missing.')
    print('')
    argument_parser.print_help()
    print('')
    return False

  if options.build_target not in build_targets:
    print('Unsupported build target: {0:s}.'.format(options.build_target))
    print('')
    argument_parser.print_help()
    print('')
    return False

  config_path = options.config_path
  if not config_path:
    config_path = os.path.dirname(__file__)
    config_path = os.path.dirname(config_path)
    config_path = os.path.join(config_path, 'data')

  if not options.preset and not options.projects:
    print('Please define a preset or projects to build.')
    print('')
    return False

  presets_file = os.path.join(config_path, 'presets.ini')
  if options.preset and not os.path.exists(presets_file):
    print('No such config file: {0:s}.'.format(presets_file))
    print('')
    return False

  projects_file = os.path.join(config_path, 'projects.ini')
  if not os.path.exists(projects_file):
    print('No such config file: {0:s}.'.format(projects_file))
    print('')
    return False

  logging.basicConfig(
      level=logging.INFO, format='[%(levelname)s] %(message)s')

  project_builder = ProjectBuilder(options.build_target)

  project_names = []
  if options.preset:
    with io.open(presets_file, 'r', encoding='utf-8') as file_object:
      preset_definition_reader = presets.PresetDefinitionReader()
      for preset_definition in preset_definition_reader.Read(file_object):
        if preset_definition.name == options.preset:
          project_names = preset_definition.project_names
          break

    if not project_names:
      print('Undefined preset: {0:s}'.format(options.preset))
      print('')
      return False

  elif options.projects:
    project_names = options.projects.split(',')

  builds = []
  disabled_packages = []
  with io.open(projects_file, 'r', encoding='utf-8') as file_object:
    project_definition_reader = projects.ProjectDefinitionReader()
    for project_definition in project_definition_reader.Read(file_object):
      if project_definition.name not in project_names:
        continue

      is_disabled = False
      if (options.build_target in project_definition.disabled or
          'all' in project_definition.disabled):
        if options.preset:
          is_disabled = True
        else:
          # If a project is manually specified ignore the disabled status.
          logging.info('Ignoring disabled status for: {0:s}'.format(
              project_definition.name))

      if is_disabled:
        disabled_packages.append(project_definition.name)
      else:
        builds.append(project_definition)

  if not os.path.exists(options.build_directory):
    os.mkdir(options.build_directory)

  current_working_directory = os.getcwd()
  os.chdir(options.build_directory)

  undefined_packages = list(project_names)
  for disabled_package in disabled_packages:
    undefined_packages.remove(disabled_package)

  failed_builds = []
  for project_definition in builds:
    if project_names and project_definition.name not in project_names:
      continue

    if undefined_packages:
      project_index = undefined_packages.index(project_definition.name)
      del undefined_packages[project_index]

    logging.info('Processing: {0:s}'.format(project_definition.name))

    # TODO: add support for dokan, bzip2
    # TODO: setup sqlite in build directory.
    if not project_builder.Build(project_definition):
      print('Failed building: {0:s}'.format(project_definition.name))
      failed_builds.append(project_definition.name)

  os.chdir(current_working_directory)

  if undefined_packages:
    print('')
    print('Undefined packages:')
    for undefined_package in undefined_packages:
      print('\t{0:s}'.format(undefined_package))

  if failed_builds:
    print('')
    print('Failed building:')
    for failed_build in failed_builds:
      print('\t{0:s}'.format(failed_build))

  return not failed_builds


if __name__ == '__main__':
  if not Main():
    sys.exit(1)
  else:
    sys.exit(0)
