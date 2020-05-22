#!/usr/bin/env python
# -*- coding: utf-8 -*-
# pylint: disable=invalid-name
"""Script to update the dependencies in various configuration files."""

from __future__ import unicode_literals

import io
import os
import sys

from l2tdevtools import dependencies
from l2tdevtools.helpers import project

from l2tdevtools.dependency_writers import appveyor_yml
from l2tdevtools.dependency_writers import check_dependencies
from l2tdevtools.dependency_writers import dependencies_py
from l2tdevtools.dependency_writers import dpkg
from l2tdevtools.dependency_writers import gift_copr
from l2tdevtools.dependency_writers import gift_ppa
from l2tdevtools.dependency_writers import jenkins_scripts
from l2tdevtools.dependency_writers import linux_scripts
from l2tdevtools.dependency_writers import macos
from l2tdevtools.dependency_writers import pylint_rc
from l2tdevtools.dependency_writers import requirements
from l2tdevtools.dependency_writers import setup
from l2tdevtools.dependency_writers import tox_ini
from l2tdevtools.dependency_writers import travis
from l2tdevtools.dependency_writers import travis_yml


def Main():
  """The main program function.

  Returns:
    bool: True if successful or False if not.
  """
  l2tdevtools_path = os.path.abspath(__file__)
  l2tdevtools_path = os.path.dirname(l2tdevtools_path)
  l2tdevtools_path = os.path.dirname(l2tdevtools_path)

  project_path = os.getcwd()
  projects_helper = project.ProjectHelper(project_path)
  project_definition = projects_helper.ReadDefinitionFile()

  dependencies_helper = dependencies.DependencyHelper()

  test_dependencies_helper = None
  if os.path.exists('test_dependencies.ini'):
    test_dependencies_helper = dependencies.DependencyHelper(
        'test_dependencies.ini')

  for writer_class in (
      pylint_rc.PylintRcWriter, travis.TravisRunWithTimeoutScriptWriter,
      requirements.RequirementsWriter, requirements.TestRequirementsWriter,
      setup.SetupCfgWriter, setup.SetupPyWriter,
      travis.TravisInstallScriptWriter, travis.TravisRunCoverageScriptWriter,
      travis.TravisRunPylintScriptWriter, travis.TravisRunPython3ScriptWriter,
      travis.TravisRunTestsScriptWriter,
      travis.TravisRunWithTimeoutScriptWriter, travis_yml.TravisYMLWriter):
    writer = writer_class(
        l2tdevtools_path, project_definition, dependencies_helper,
        test_dependencies_helper)
    writer.Write()

  for writer_class in (
      appveyor_yml.AppveyorYmlWriter,
      check_dependencies.CheckDependenciesWriter,
      dependencies_py.DependenciesPyWriter, dpkg.DPKGCompatWriter,
      dpkg.DPKGControlWriter, dpkg.DPKGRulesWriter,
      gift_copr.GIFTCOPRInstallScriptWriter,
      gift_ppa.GIFTPPAInstallScriptPY3Writer,
      jenkins_scripts.LinuxRunEndToEndTestsScriptWriter,
      jenkins_scripts.RunPython3EndToEndTestsScriptWriter,
      linux_scripts.UbuntuInstallationScriptWriter,
      macos.MacOSInstallScriptWriter, macos.MacOSMakeDistScriptWriter,
      macos.MacOSUninstallScriptWriter, tox_ini.ToxIniWriter):
    if not os.path.exists(writer_class.PATH):
      continue

    writer = writer_class(
        l2tdevtools_path, project_definition, dependencies_helper,
        test_dependencies_helper)
    writer.Write()

  output_path = os.path.join('utils', 'dependencies.py')
  if os.path.exists(output_path):
    input_path = os.path.join(
        l2tdevtools_path, 'l2tdevtools', 'dependencies.py')
    file_data = []
    with io.open(input_path, 'r', encoding='utf-8') as file_object:
      for line in file_object.readlines():
        if 'GetDPKGDepends' in line:
          break

        file_data.append(line)

    file_data.pop()
    file_data = ''.join(file_data)

    with io.open(output_path, 'w', encoding='utf-8') as file_object:
      file_object.write(file_data)

  # Remove old scripts.
  script_path = os.path.join('config', 'linux', 'gift_ppa_install.sh')
  if os.path.isfile(script_path):
    os.remove(script_path)

  return True


if __name__ == '__main__':
  if not Main():
    sys.exit(1)
  else:
    sys.exit(0)
