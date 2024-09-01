#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Script to automate creating builds of projects."""

import argparse
import io
import logging
import os
import platform
import subprocess
import sys

from l2tdevtools import download_helper
from l2tdevtools import presets
from l2tdevtools import projects
from l2tdevtools import source_helper
from l2tdevtools.build_helpers import factory as build_helper


# Since os.path.abspath() uses the current working directory (cwd)
# os.path.abspath(__file__) will point to a different location if
# cwd has been changed. Hence we preserve the absolute location of __file__.
__file__ = os.path.abspath(__file__)


# TODO: look into merging functionality with update script.

class ProjectBuilder(object):
  """Class that helps in building projects.

  Attributes:
    project_definitions (dict[str, ProjectDefinition]): project definitions.
  """

  # The distributions to build dpkg-source packages for.
  _DPKG_SOURCE_DISTRIBUTIONS = frozenset(['noble'])

  def __init__(self, build_target, l2tdevtools_path, downloads_directory):
    """Initializes the project builder.

    Args:
      build_target (str): build target.
      l2tdevtools_path (str): path to l2tdevtools.
      downloads_directory (str): path to the directory where projects are
          downloaded.
    """
    super(ProjectBuilder, self).__init__()
    self._build_helpers = {}
    self._build_target = build_target
    self._downloads_directory = downloads_directory
    self._l2tdevtools_path = l2tdevtools_path
    self._source_helpers = {}

    self.project_definitions = {}

  def _BuildProject(
      self, build_helper_object, source_helper_object, distribution):
    """Builds a project.

    Args:
      build_helper_object (BuildHelper): build helper.
      source_helper_object (SourceHelper): source helper.
      distribution (str): name of the distribution or None if not available.

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
      logging.warning(
          f'Build of: {source_helper_object.project_name:s} failed.')
    else:
      log_filename = '_'.join([
          source_helper_object.project_name, build_helper_object.LOG_FILENAME])

      # Remove older logfiles if they exists otherwise the rename
      # fails on Windows.
      if os.path.exists(log_filename):
        os.remove(log_filename)

      os.rename(build_helper_object.LOG_FILENAME, log_filename)
      logging.warning((
          f'Build of: {source_helper_object.project_name:s} failed, for more '
          f'information check {log_filename:s}'))

    return False

  def _ExpandPresets(self, preset_definitions, preset_names):
    """Expands preset names to project names.

    Args:
      preset_definitions (dict[str, PresetDefinition]): preset definitions.
      preset_names (str): names of the presets to expand.

    Returns:
      set[str]: project names.
    """
    project_names = set()
    for preset_name in preset_names:
      preset_definition = preset_definitions.get(preset_name, None)
      if not preset_definition:
        continue

      if preset_definition.preset_names:
        sub_project_names = self._ExpandPresets(
            preset_definitions, preset_definition.preset_names)
        project_names = project_names.union(sub_project_names)

      project_names = project_names.union(
          set(preset_definition.project_names))

    return project_names

  def Build(self, project_definition, distributions=None):
    """Builds a project.

    Args:
      project_definition (ProjectDefinition): project definition.
      distributions (Optional[list[str]]): distributions to build.

    Returns:
      bool: True if the build is successful or False on error.
    """
    build_helper_object = self._build_helpers.get(
        project_definition.name, None)
    if not build_helper_object:
      logging.warning('Missing build helper.')
      return False

    source_helper_object = self._source_helpers.get(
        project_definition.name, None)
    if not source_helper_object:
      logging.warning('Missing source helper.')
      return False

    if not distributions:
      if self._build_target == 'dpkg-source':
        distributions = self._DPKG_SOURCE_DISTRIBUTIONS
      else:
        distributions = [None]

    for distribution in distributions:
      if not self._BuildProject(
          build_helper_object, source_helper_object, distribution):
        return False

    if os.path.exists(build_helper_object.LOG_FILENAME):
      logging.info(f'Removing: {build_helper_object.LOG_FILENAME:s}')
      os.remove(build_helper_object.LOG_FILENAME)

    return True

  def CheckBuildDependencies(self, project_definition):
    """Checks if the build dependencies of a project are met.

    Args:
      project_definition (ProjectDefinition): project definition.

    Returns:
      list[str]: build dependency names that are not met or an empty list.
    """
    source_helper_object = self._source_helpers.get(
        project_definition.name, None)
    if not source_helper_object:
      logging.warning('Missing source helper.')
      return []

    source_package_path = source_helper_object.GetSourcePackagePath()
    if not source_package_path:
      logging.info('Missing source package of: {0:s}'.format(
          source_helper_object.project_name))
      return []

    if not source_helper_object.Create():
      source_filename = source_helper_object.GetSourcePackageFilename()
      logging.error('Extraction of source package: {0:s} failed'.format(
          source_filename))
      return []

    source_directory = source_helper_object.GetSourceDirectoryPath()
    if not source_directory:
      logging.info('Missing source directory of: {0:s}'.format(
          source_helper_object.project_name))
      return []

    if not project_definition.build_system:
      if os.path.exists(os.path.join(source_directory, 'configure')):
        project_definition.build_system = 'configure_make'
      elif os.path.exists(os.path.join(source_directory, 'setup.py')):
        project_definition.build_system = 'setup_py'
      elif os.path.exists(os.path.join(source_directory, 'pyproject.toml')):
        project_definition.build_system = 'pyproject'
      else:
        logging.warning('Unable to determine build system of: {0:s}'.format(
            project_definition.name))
        return []

    build_helper_object = build_helper.BuildHelperFactory.NewBuildHelper(
        project_definition, self._build_target, self._l2tdevtools_path,
        self.project_definitions)
    if not build_helper_object:
      logging.warning('Unable to determine how to build: {0:s}'.format(
          project_definition.name))
      return []

    self._build_helpers[project_definition.name] = build_helper_object

    return build_helper_object.CheckBuildDependencies()

  def CheckProjectConfiguration(self, project_definition):
    """Checks if the project configuration is correct.

    Args:
      project_definition (ProjectDefinition): project definition.

    Returns:
      bool: True if the project configuration is correct, False otherwise.
    """
    build_helper_object = self._build_helpers.get(
        project_definition.name, None)
    if not build_helper_object:
      logging.warning('Missing build helper.')
      return False

    return build_helper_object.CheckProjectConfiguration()

  def Download(self, project_definition):
    """Downloads the source package of a project.

    Args:
      project_definition (ProjectDefinition): project definition.

    Returns:
      bool: True if the download is successful or False on error.

    Raises:
      ValueError: if the project download URL is not supported.
    """
    download_helper_object = (
        download_helper.DownloadHelperFactory.NewDownloadHelper(
            project_definition))

    source_helper_object = source_helper.SourcePackageHelper(
        project_definition.name, project_definition, self._downloads_directory,
        download_helper_object)

    source_helper_object.Clean()

    # TODO: add a step to make sure build environment is sane
    # e.g. _CheckStatusIsClean()

    source_package_path = source_helper_object.Download()

    if self._build_target == 'download':
      # If available run the script post-download.sh after download.
      if os.path.exists('post-download.sh'):
        command = 'sh ./post-download.sh {0:s}'.format(source_package_path)
        exit_code = subprocess.call(command, shell=True)
        if exit_code != 0:
          logging.error('Running: "{0:s}" failed.'.format(command))
          return False

    self._source_helpers[project_definition.name] = source_helper_object

    return True

  def ReadProjectDefinitions(self, path):
    """Reads project definitions.

    Args:
      path (str): path of the project definitions file.
    """
    with io.open(path, 'r', encoding='utf-8') as file_object:
      project_definition_reader = projects.ProjectDefinitionReader()
      self.project_definitions = {
          definition.name: definition
          for definition in project_definition_reader.Read(file_object)}

  def ReadProjectsPreset(self, path, preset_name):
    """Reads a projects preset from the preset file.

    Args:
      path (str): path of the projects preset file.
      preset_name (str): name of the preset.

    Returns:
      list[str]: names of the projects defined by the preset or an empty list
          if the preset was not defined.
    """
    preset_definitions = {}

    with io.open(path, 'r', encoding='utf-8') as file_object:
      definition_reader = presets.PresetDefinitionReader()
      preset_definitions = {
          preset_definition.name: preset_definition
          for preset_definition in definition_reader.Read(file_object)}

    return list(self._ExpandPresets(preset_definitions, [preset_name]))


def Main():
  """The main program function.

  Returns:
    bool: True if successful or False if not.
  """
  build_targets = frozenset([
      'download', 'dpkg', 'dpkg-source', 'rpm', 'source', 'srpm', 'wheel'])

  argument_parser = argparse.ArgumentParser(description=(
      'Downloads and builds the latest versions of projects.'))

  argument_parser.add_argument(
      'build_target', choices=sorted(build_targets), action='store',
      metavar='BUILD_TARGET', default=None, help='The build target.')

  default_builds_directory = os.path.join('..', 'l2tbuilds')
  argument_parser.add_argument(
      '--build-directory', '--builds-directory', '--build_directory',
      '--builds_directory', action='store', metavar='DIRECTORY',
      dest='builds_directory', type=str, default=default_builds_directory,
      help='The location of the build directory.')

  argument_parser.add_argument(
      '-c', '--config', dest='config_path', action='store',
      metavar='CONFIG_PATH', default=None, help=(
          'path of the directory containing the build configuration '
          'files e.g. projects.ini.'))

  argument_parser.add_argument(
      '--distributions', dest='distributions', action='store',
      metavar='NAME(S)', default='', help=(
          'comma separated list of specific distribution names to build.'))

  argument_parser.add_argument(
      '--download-directory', '--downloads-directory', '--download_directory',
      '--downloads_directory', action='store', metavar='DIRECTORY',
      dest='downloads_directory', type=str,
      default=None, help='The location of the downloads directory.')

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
    l2tdevtools_path = os.path.dirname(__file__)
    l2tdevtools_path = os.path.dirname(l2tdevtools_path)
    config_path = os.path.join(l2tdevtools_path, 'data')

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

  if os.path.abspath(options.builds_directory).startswith(l2tdevtools_path):
    print(('Builds directory cannot be within l2tdevtools directory due to '
           'usage of pbr'))
    print('')
    return False

  logging.basicConfig(
      level=logging.INFO, format='[%(levelname)s] %(message)s')

  distributions = options.distributions.split(',') or None

  if not options.downloads_directory:
    options.downloads_directory = options.builds_directory

  project_builder = ProjectBuilder(
      options.build_target, l2tdevtools_path, options.downloads_directory)

  project_names = []
  if options.preset:
    project_names = project_builder.ReadProjectsPreset(
        presets_file, options.preset)
    if not project_names:
      print('Undefined preset: {0:s}'.format(options.preset))
      print('')
      return False

  elif options.projects:
    project_names = options.projects.split(',')

  project_builder.ReadProjectDefinitions(projects_file)

  operating_system = platform.system().lower()

  builds = []
  disabled_projects = []
  for name, definition in project_builder.project_definitions.items():
    if name not in project_names:
      continue

    is_disabled = False
    if (options.build_target in definition.disabled or
        operating_system in definition.disabled or
        'all' in definition.disabled):
      if options.preset:
        is_disabled = True
      else:
        # If a project is manually specified ignore the disabled status.
        logging.info('Ignoring disabled status for: {0:s}'.format(name))

    if is_disabled:
      disabled_projects.append(name)
    else:
      builds.append(definition)

  if not os.path.exists(options.builds_directory):
    os.mkdir(options.builds_directory)

  if not os.path.exists(options.downloads_directory):
    os.mkdir(options.downloads_directory)

  undefined_projects = set(project_names)
  for disabled_package in disabled_projects:
    undefined_projects.remove(disabled_package)

  configuration_errors = set()
  failed_builds = set()
  failed_downloads = set()
  missing_build_dependencies = set()

  for project_definition in list(builds):
    if project_names and project_definition.name not in project_names:
      builds.remove(project_definition)
      continue

    undefined_projects.remove(project_definition.name)

    if not project_builder.Download(project_definition):
      builds.remove(project_definition)

      print('Failed downloading: {0:s}'.format(project_definition.name))
      failed_downloads.add(project_definition.name)

  if options.build_target != 'download':
    current_working_directory = os.getcwd()
    os.chdir(options.builds_directory)

    try:
      for project_definition in list(builds):
        dependencies = project_builder.CheckBuildDependencies(
            project_definition)

        if dependencies:
          builds.remove(project_definition)

          print(
              'Unable to build: {0:s} missing build dependencies: {1:s}'.format(
                  project_definition.name, ', '.join(dependencies)))
          missing_build_dependencies.update(dependencies)

        if not project_builder.CheckProjectConfiguration(project_definition):
          print('Detected error in configuration of: {0:s}'.format(
              project_definition.name))
          configuration_errors.add(project_definition.name)

      for project_definition in list(builds):
        logging.info('Building: {0:s}'.format(project_definition.name))

        # TODO: add support for dokan, bzip2
        # TODO: setup sqlite in build directory.
        if not project_builder.Build(
            project_definition, distributions=distributions):
          print('Failed building: {0:s}'.format(project_definition.name))
          failed_builds.add(project_definition.name)

    finally:
      os.chdir(current_working_directory)

  if undefined_projects:
    print('')
    print('Undefined projects:')
    for name in sorted(undefined_projects):
      print('\t{0:s}'.format(name))

  if configuration_errors:
    print('')
    print('Projects with configuration errors:')
    for name in sorted(configuration_errors):
      print('\t{0:s}'.format(name))

  if failed_downloads:
    print('')
    print('Failed downloading:')
    for name in sorted(failed_downloads):
      print('\t{0:s}'.format(name))

  if missing_build_dependencies:
    print('')
    print('Missing build dependencies:')
    for dependency in sorted(missing_build_dependencies):
      print('\t{0:s}'.format(dependency))

  if failed_builds:
    print('')
    print('Failed building:')
    for name in sorted(failed_builds):
      print('\t{0:s}'.format(name))

  return (not failed_downloads and not missing_build_dependencies and
          not failed_builds)


if __name__ == '__main__':
  if not Main():
    sys.exit(1)
  else:
    sys.exit(0)
