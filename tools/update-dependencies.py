#!/usr/bin/env python
# -*- coding: utf-8 -*-
# pylint: disable=invalid-name
"""Script to update the dependencies in various configuration files."""

from __future__ import unicode_literals

import os
import sys

from l2tdevtools import dependencies
from l2tdevtools.helpers import project

from l2tdevtools.dependency_writers import appveyor_yml
from l2tdevtools.dependency_writers import dependencies_py
from l2tdevtools.dependency_writers import dpkg
from l2tdevtools.dependency_writers import gift_copr
from l2tdevtools.dependency_writers import gift_ppa
from l2tdevtools.dependency_writers import macos
from l2tdevtools.dependency_writers import pylint_rc
from l2tdevtools.dependency_writers import requirements_txt
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

  helper = dependencies.DependencyHelper()

  for writer_class in (
      appveyor_yml.AppveyorYmlWriter, pylint_rc.PylintRcWriter,
      travis.TravisRunWithTimeoutScriptWriter,
      requirements_txt.RequirementsWriter, setup.SetupCfgWriter,
      setup.SetupPyWriter, tox_ini.ToxIniWriter,
      travis.TravisInstallScriptWriter, travis.TravisRunTestsScriptWriter,
      travis.TravisRunWithTimeoutScriptWriter, travis_yml.TravisYMLWriter):
    writer = writer_class(l2tdevtools_path, project_definition, helper)
    writer.Write()

  for writer_class in (
      dependencies_py.DependenciesPyWriter, dpkg.DPKGControlWriter,
      gift_copr.GIFTCOPRInstallScriptWriter,
      gift_ppa.GIFTPPAInstallScriptWriter,
      macos.MacOSInstallScriptWriter,
      macos.MacOSMakeDistScriptWriter, macos.MacOSUninstallScriptWriter):
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

  return True


if __name__ == '__main__':
  if not Main():
    sys.exit(1)
  else:
    sys.exit(0)
