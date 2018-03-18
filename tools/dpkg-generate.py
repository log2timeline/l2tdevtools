#!/usr/bin/env python
# -*- coding: utf-8 -*-
# pylint: disable=invalid-name
"""Script to generate dpkg packaging files."""

from __future__ import print_function
from __future__ import unicode_literals

import argparse
import glob
import logging
import os
import sys

from l2tdevtools import dpkg_files
from l2tdevtools import projects


def Main():
  """The main program function.

  Returns:
    A boolean containing True if successful or False if not.
  """
  argument_parser = argparse.ArgumentParser(description=(
      'Generates dpkg packaging files for a project.'))

  argument_parser.add_argument(
      'project_name', action='store', metavar='NAME', type=str, help=(
          'Project name for which the dpkg packaging files should be '
          'generated.'))

  argument_parser.add_argument(
      '-c', '--config', dest='config_file', action='store',
      metavar='CONFIG_FILE', default=None,
      help='path of the build configuration file.')

  argument_parser.add_argument(
      '--source-directory', '--source_directory', action='store',
      metavar='DIRECTORY', dest='source_directory', type=str,
      default=None, help='The location of the the source directory.')

  options = argument_parser.parse_args()

  logging.basicConfig(
      level=logging.INFO, format='[%(levelname)s] %(message)s')

  if not options.config_file:
    options.config_file = os.path.dirname(__file__)
    options.config_file = os.path.dirname(options.config_file)
    options.config_file = os.path.join(
        options.config_file, 'data', 'projects.ini')

  if not os.path.exists(options.config_file):
    print('No such config file: {0:s}.'.format(options.config_file))
    print('')
    return False

  project_definition_match = None
  with open(options.config_file) as file_object:
    project_definition_reader = projects.ProjectDefinitionReader()
    for project_definition in project_definition_reader.Read(file_object):
      if options.project_name == project_definition.name:
        project_definition_match = project_definition

  if not project_definition_match:
    print('No such package name: {0:s}.'.format(options.project_name))
    print('')
    return False

  source_path = options.source_directory
  if not source_path:
    globbed_paths = []
    for path in glob.glob('{0:s}*'.format(options.project_name)):
      if not os.path.isdir(path):
        continue
      globbed_paths.append(path)

    if not len(globbed_paths) == 1:
      print('Unable to determine source directory.')
      print('')
      return False

    source_path = globbed_paths[0]

  if not os.path.exists(source_path):
    print('No such source directory: {0:s}.'.format(source_path))
    print('')
    return False

  source_path = os.path.abspath(source_path)
  project_version = os.path.basename(source_path)
  if not project_version.startswith('{0:s}-'.format(options.project_name)):
    print((
        'Unable to determine project version based on source '
        'directory: {0:s}.').format(source_path))
    print('')
    return False

  _, _, project_version = project_version.partition('-')

  dpkg_path = os.path.join(source_path, 'dpkg')
  if os.path.exists(dpkg_path):
    print('Destination dpkg directory: {0:s} already exists.'.format(
        dpkg_path))
    print('')
    return False

  tools_path = os.path.dirname(__file__)
  data_path = os.path.join(os.path.dirname(tools_path), 'data')

  build_files_generator = dpkg_files.DPKGBuildFilesGenerator(
      options.project_name, project_version,
      project_definition_match, data_path)

  print('Generating dpkg files for: {0:s} {1:s} in: {2:s}'.format(
      options.project_name, project_version, dpkg_path))
  build_files_generator.GenerateFiles(dpkg_path)
  print('')

  return True


if __name__ == '__main__':
  if not Main():
    sys.exit(1)
  else:
    sys.exit(0)
