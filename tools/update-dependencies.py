#!/usr/bin/env python
# -*- coding: utf-8 -*-
# pylint: disable=invalid-name
"""Script to update the dependencies in various configuration files."""

import io
import os
import shutil
import sys

from l2tdevtools import dependencies
from l2tdevtools.helpers import project

from l2tdevtools.dependency_writers import appveyor_scripts
from l2tdevtools.dependency_writers import appveyor_yml
from l2tdevtools.dependency_writers import check_dependencies
from l2tdevtools.dependency_writers import dependencies_py
from l2tdevtools.dependency_writers import dpkg
from l2tdevtools.dependency_writers import github_actions
from l2tdevtools.dependency_writers import gift_copr
from l2tdevtools.dependency_writers import gift_ppa
from l2tdevtools.dependency_writers import jenkins_scripts
from l2tdevtools.dependency_writers import linux_scripts
from l2tdevtools.dependency_writers import pylint_rc
from l2tdevtools.dependency_writers import requirements
from l2tdevtools.dependency_writers import setup
from l2tdevtools.dependency_writers import sphinx_docs
from l2tdevtools.dependency_writers import tox_ini


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

  for writer_class in (
      pylint_rc.PylintRcWriter, requirements.RequirementsWriter,
      requirements.TestRequirementsWriter, setup.SetupCfgWriter,
      setup.SetupPyWriter):
    writer = writer_class(
        l2tdevtools_path, project_definition, dependencies_helper)
    writer.Write()

  for writer_class in (
      github_actions.GitHubActionsTestDockerYmlWriter,
      github_actions.GitHubActionsTestToxYmlWriter,
      appveyor_scripts.AppVeyorInstallPS1ScriptWriter,
      appveyor_scripts.AppVeyorInstallSHScriptWriter,
      appveyor_scripts.AppVeyorRuntestsSHScriptWriter,
      appveyor_yml.AppveyorYmlWriter,
      check_dependencies.CheckDependenciesWriter,
      dependencies_py.DependenciesPyWriter, dpkg.DPKGCompatWriter,
      dpkg.DPKGControlWriter, dpkg.DPKGRulesWriter,
      gift_copr.GIFTCOPRInstallScriptWriter,
      gift_ppa.GIFTPPAInstallScriptWriter,
      jenkins_scripts.LinuxRunEndToEndTestsScriptWriter,
      jenkins_scripts.RunPython3EndToEndTestsScriptWriter,
      linux_scripts.UbuntuInstallationScriptWriter,
      sphinx_docs.SphinxBuildConfigurationWriter,
      sphinx_docs.SphinxBuildRequirementsWriter, tox_ini.ToxIniWriter):
    if not os.path.exists(writer_class.PATH):
      continue

    writer = writer_class(
        l2tdevtools_path, project_definition, dependencies_helper)
    writer.Write()

  output_path = os.path.join('utils', 'dependencies.py')
  if os.path.exists(output_path):
    input_path = os.path.join(
        l2tdevtools_path, 'l2tdevtools', 'dependencies.py')
    file_data = []
    with io.open(input_path, 'r', encoding='utf-8') as file_object:
      for line in file_object.readlines():
        if '# The following functions should not be included in ' in line:
          break

        file_data.append(line)

    file_data.pop()
    file_data = ''.join(file_data)

    with io.open(output_path, 'w', encoding='utf-8') as file_object:
      file_object.write(file_data)

  # Remove old configurations and scripts.
  script_path = os.path.join('config', 'linux', 'gift_ppa_install.sh')
  if os.path.isfile(script_path):
    os.remove(script_path)

  script_path = os.path.join('config', 'macos')
  if os.path.isfile(script_path):
    shutil.rmtree(script_path)

  script_path = os.path.join('.travis.yml')
  if os.path.isfile(script_path):
    os.remove(script_path)

  script_path = os.path.join('config', 'travis')
  if os.path.isfile(script_path):
    shutil.rmtree(script_path)

  return True


if __name__ == '__main__':
  if not Main():
    sys.exit(1)
  else:
    sys.exit(0)
