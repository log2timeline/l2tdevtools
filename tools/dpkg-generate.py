#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Script to generate dpkg packaging files."""

from __future__ import print_function
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
      u'Generates dpkg packaging files for a project.'))

  argument_parser.add_argument(
      u'project_name', action=u'store', metavar=u'NAME', type=str, help=(
          u'Project name for which the dpkg packaging files should be '
          u'generated.'))

  argument_parser.add_argument(
      u'-c', u'--config', dest=u'config_file', action=u'store',
      metavar=u'CONFIG_FILE', default=None,
      help=u'path of the build configuration file.')

  argument_parser.add_argument(
      u'--source-directory', u'--source_directory', action=u'store',
      metavar=u'DIRECTORY', dest=u'source_directory', type=str,
      default=None, help=u'The location of the the source directory.')

  options = argument_parser.parse_args()

  logging.basicConfig(
      level=logging.INFO, format=u'[%(levelname)s] %(message)s')

  if not options.config_file:
    options.config_file = os.path.dirname(__file__)
    options.config_file = os.path.dirname(options.config_file)
    options.config_file = os.path.join(
        options.config_file, u'data', u'projects.ini')

  if not os.path.exists(options.config_file):
    print(u'No such config file: {0:s}.'.format(options.config_file))
    print(u'')
    return False

  project_definition_match = None
  with open(options.config_file) as file_object:
    project_definition_reader = projects.ProjectDefinitionReader()
    for project_definition in project_definition_reader.Read(file_object):
      if options.project_name == project_definition.name:
        project_definition_match = project_definition

  if not project_definition_match:
    print(u'No such package name: {0:s}.'.format(options.project_name))
    print(u'')
    return False

  source_path = options.source_directory
  if not source_path:
    globbed_paths = []
    for path in glob.glob(u'{0:s}*'.format(options.project_name)):
      if not os.path.isdir(path):
        continue
      globbed_paths.append(path)

    if not len(globbed_paths) == 1:
      print(u'Unable to determine source directory.')
      print(u'')
      return False

    source_path = globbed_paths[0]

  if not os.path.exists(source_path):
    print(u'No such source directory: {0:s}.'.format(source_path))
    print(u'')
    return False

  source_path = os.path.abspath(source_path)
  project_version = os.path.basename(source_path)
  if not project_version.startswith(u'{0:s}-'.format(options.project_name)):
    print((
        u'Unable to determine project version based on source '
        u'directory: {0:s}.').format(source_path))
    print(u'')
    return False

  _, _, project_version = project_version.partition(u'-')

  dpkg_path = os.path.join(source_path, u'dpkg')
  if os.path.exists(dpkg_path):
    print(u'Destination dpkg directory: {0:s} already exists.'.format(
        dpkg_path))
    print(u'')
    return False

  tools_path = os.path.dirname(__file__)
  data_path = os.path.join(os.path.dirname(tools_path), u'data')

  build_files_generator = dpkg_files.DPKGBuildFilesGenerator(
      options.project_name, project_version,
      project_definition_match, data_path)

  print(u'Generating dpkg files for: {0:s} {1:s} in: {2:s}'.format(
      options.project_name, project_version, dpkg_path))
  build_files_generator.GenerateFiles(dpkg_path)
  print(u'')

  return True


if __name__ == '__main__':
  if not Main():
    sys.exit(1)
  else:
    sys.exit(0)
