#!/usr/bin/env python
# -*- coding: utf-8 -*-
# pylint: disable=invalid-name
"""Script to update the dependencies in various configuration files."""

from __future__ import unicode_literals

import os

from l2tdevtools import dependencies
from l2tdevtools import project_config
from l2tdevtools.helpers import project

from l2tdevtools.dependency_writers import appveyor_yml
from l2tdevtools.dependency_writers import dependencies_py
from l2tdevtools.dependency_writers import dpkg_control
from l2tdevtools.dependency_writers import gift_copr_install
from l2tdevtools.dependency_writers import pylint_rc
from l2tdevtools.dependency_writers import requirements_txt
from l2tdevtools.dependency_writers import setup_cfg
from l2tdevtools.dependency_writers import travis_install
from l2tdevtools.dependency_writers import travis_run_with_timeout
from l2tdevtools.dependency_writers import travis_runtests
from l2tdevtools.dependency_writers import travis_yml
from l2tdevtools.dependency_writers import gift_ppa_install
from l2tdevtools.dependency_writers import tox_ini


if __name__ == '__main__':
  l2tdevtools_path = os.path.abspath(__file__)
  l2tdevtools_path = os.path.dirname(l2tdevtools_path)
  l2tdevtools_path = os.path.dirname(l2tdevtools_path)

  project_path = os.getcwd()
  projects_helper = project.ProjectHelper(project_path)

  project_file = '{0:s}.ini'.format(projects_helper.project_name)

  project_reader = project_config.ProjectDefinitionReader()
  with open(project_file, 'rb') as file_object:
    project_definition = project_reader.Read(file_object)

  helper = dependencies.DependencyHelper()

  for writer_class in (
      appveyor_yml.AppveyorYmlWriter, pylint_rc.PylintRcWriter,
      requirements_txt.RequirementsWriter, setup_cfg.SetupCfgWriter,
      travis_install.TravisInstallScriptWriter,
      travis_run_with_timeout.TravisRunWithTimeoutScriptWriter,
      travis_runtests.TravisRunTestsScriptWriter, travis_yml.TravisYMLWriter,
      tox_ini.ToxIniWriter):
    writer = writer_class(l2tdevtools_path, project_definition, helper)
    writer.Write()

  for writer_class in (
      dependencies_py.DependenciesPyWriter, dpkg_control.DPKGControlWriter,
      gift_copr_install.GIFTCOPRInstallScriptWriter,
      gift_ppa_install.GIFTPPAInstallScriptWriter):
    if not os.path.exists(writer_class.PATH):
      continue

    writer = writer_class(l2tdevtools_path, project_definition, helper)
    writer.Write()

  path = os.path.join(l2tdevtools_path, 'l2tdevtools', 'dependencies.py')
  file_data = []
  with open(path, 'rb') as file_object:
    for line in file_object.readlines():
      if 'GetDPKGDepends' in line:
        break

      file_data.append(line)

  file_data.pop()
  file_data = ''.join(file_data)

  path = os.path.join('utils', 'dependencies.py')
  with open(path, 'wb') as file_object:
    file_object.write(file_data)
