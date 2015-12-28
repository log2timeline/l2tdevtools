#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Script to generate dpkg packaging files."""

from __future__ import print_function
import argparse
import logging
import sys

from l2tdevtools import dependencies
from l2tdevtools import dpkg_files


def Main():
  argument_parser = argparse.ArgumentParser(description=(
      u'Generates dpkg packaging files for a project.'))

  argument_parser.add_argument(
      u'project_name', action=u'store', metavar=u'NAME', type=unicode, help=(
          u'Project name for which the dpkg packaging files should be '
          u'generated.'))

  argument_parser.add_argument(
      u'-c', u'--config', dest=u'config_file', action=u'store',
      metavar=u'CONFIG_FILE', default=None,
      help=u'path of the build configuration file.')

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

  dependency_definition_match = None
  with open(options.config_file) as file_object:
    dependency_definition_reader = dependencies.DependencyDefinitionReader()
    for dependency_definition in dependency_definition_reader.Read(file_object):
      if options.project_name == dependency_definition.name:
        dependency_definition_match = dependency_definition

  if not dependency_definition_match:
    print(u'No such package name: {0:s}.'.format(options.project_name))
    print(u'')
    return False

  build_files_generator = dpkg_files.DpkgBuildFilesGenerator(
      options.project_name, source_helper.project_version,
      dependency_definition_match)
  build_files_generator.GenerateFiles(u'dpkg')

  return True


if __name__ == '__main__':
  if not Main():
    sys.exit(1)
  else:
    sys.exit(0)
