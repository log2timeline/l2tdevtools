# -*- coding: utf-8 -*-
"""Helper for building projects from source."""

from __future__ import unicode_literals

import glob
import logging
import os
import re
import shlex
import shutil
import subprocess

from l2tdevtools.build_helpers import interface
from l2tdevtools import spec_file


class OSCBuildHelper(interface.BuildHelper):
  """Helper to build with osc for the openSUSE build service."""

  _OSC_PROJECT = 'home:joachimmetz:testing'

  _OSC_PACKAGE_METADATA = (
      '<package name="{name:s}" project="{project:s}">\n'
      '  <title>{title:s}</title>\n'
      '  <description>{description:s}</description>\n'
      '</package>\n')

  def _BuildPrepare(self, source_helper_object):
    """Prepares the source for building with osc.

    Args:
      source_helper_object (SourceHelper): source helper.
    """
    # Checkout the project if it does not exist otherwise make sure
    # the project files are up to date.
    if not os.path.exists(self._OSC_PROJECT):
      if not self._OSCCheckout():
        return

    else:
      if not self._OSCUpdate():
        return False

    # Create a package of the project if it does not exist.
    osc_package_path = os.path.join(
        self._OSC_PROJECT, source_helper_object.project_name)
    if os.path.exists(osc_package_path):
      return True

    if not self._OSCCreatePackage(source_helper_object):
      return False

    if not self._OSCUpdate():
      return False

    return True

  def _CheckStatusIsClean(self):
    """Runs osc status to check if the status is clean.

    Returns:
      bool: True if successful, False otherwise.
    """
    command = 'osc status {0:s}'.format(self._OSC_PROJECT)
    arguments = shlex.split(command)
    process = subprocess.Popen(
        arguments, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
    if not process:
      logging.error('Running: "{0:s}" failed.'.format(command))
      return False

    output, error = process.communicate()
    if process.returncode != 0:
      logging.error('Running: "{0:s}" failed with error: {1!s}.'.format(
          command, error))
      return False

    if output:
      logging.error('Unable to continue with pending changes.')
      return False

    return True

  def _OSCAdd(self, path):
    """Runs osc add to add a new file.

    Args:
      path (str): path of the file to add, relative to the osc project
          directory.

    Returns:
      bool: True if successful, False otherwise.
    """
    log_file_path = os.path.join('..', self.LOG_FILENAME)
    command = 'osc -q add {0:s} >> {1:s} 2>&1'.format(path, log_file_path)
    exit_code = subprocess.call('(cd {0:s} && {1:s})'.format(
        self._OSC_PROJECT, command), shell=True)
    if exit_code != 0:
      logging.error('Running: "{0:s}" failed.'.format(command))
      return False

    return True

  def _OSCCheckout(self):
    """Runs osc checkout.

    Returns:
      bool: True if successful, False otherwise.
    """
    command = 'osc -q checkout {0:s} >> {1:s} 2>&1 '.format(
        self._OSC_PROJECT, self.LOG_FILENAME)
    exit_code = subprocess.call(command, shell=True)
    if exit_code != 0:
      logging.error('Running: "{0:s}" failed.'.format(command))
      return False

    return True

  def _OSCCommit(self, package_name):
    """Runs osc commit.

    Args:
      package_name (str): name of the package.

    Returns:
      bool: True if successful, False otherwise.
    """
    # Running osc commit from the package sub directory is more efficient.
    osc_project_path = os.path.join(self._OSC_PROJECT, package_name)
    log_file_path = os.path.join('..', '..', self.LOG_FILENAME)
    command = 'osc -q commit -n >> {0:s} 2>&1'.format(log_file_path)
    exit_code = subprocess.call('(cd {0:s} && {1:s})'.format(
        osc_project_path, command), shell=True)
    if exit_code != 0:
      logging.error('Running: "{0:s}" failed.'.format(command))
      return False

    return True

  def _OSCCreatePackage(self, source_helper_object):
    """Runs osc meta pkg to create a new package.

    Args:
      source_helper_object (SourceHelper): source helper.

    Returns:
      bool: True if successful, False otherwise.
    """
    template_values = {
        'description': source_helper_object.project_name,
        'name': source_helper_object.project_name,
        'project': self._OSC_PROJECT,
        'title': source_helper_object.project_name}

    package_metadata = self._OSC_PACKAGE_METADATA.format(**template_values)

    command = (
        'osc -q meta pkg -F - {0:s} {1:s} << EOI\n{2:s}\nEOI\n').format(
            self._OSC_PROJECT, source_helper_object.project_name,
            package_metadata)
    exit_code = subprocess.call('(cd {0:s} && {1:s})'.format(
        self._OSC_PROJECT, command), shell=True)
    if exit_code != 0:
      logging.error('Running: "{0:s}" failed.'.format(command))
      return False

    return True

  def _OSCUpdate(self):
    """Runs osc update.

    Returns:
      bool: True if successful, False otherwise.
    """
    log_file_path = os.path.join('..', self.LOG_FILENAME)
    command = 'osc -q update >> {0:s} 2>&1'.format(log_file_path)
    exit_code = subprocess.call('(cd {0:s} && {1:s})'.format(
        self._OSC_PROJECT, command), shell=True)
    if exit_code != 0:
      logging.error('Running: "{0:s}" failed.'.format(command))
      return False

    return True

  def CheckBuildDependencies(self):
    """Checks if the build dependencies are met.

    Returns:
      list[str]: build dependency names that are not met or an empty list.
    """
    # Dependencies are handled by the openSUSE build service.
    return []

  def Clean(self, source_helper_object):
    """Cleans the build and dist directory.

    Args:
      source_helper_object (SourceHelper): source helper.
    """
    project_version = source_helper_object.GetProjectVersion()

    osc_package_path = os.path.join(
        self._OSC_PROJECT, source_helper_object.project_name)
    osc_source_filename = '{0:s}-{1!s}.tar.gz'.format(
        source_helper_object.project_name, project_version)

    filenames_to_ignore = '^{0:s}'.format(
        os.path.join(osc_package_path, osc_source_filename))
    filenames_to_ignore = re.compile(filenames_to_ignore)

    # Remove files of previous versions in the format:
    # project-version.tar.gz
    osc_source_filename_glob = '{0:s}-*.tar.gz'.format(
        source_helper_object.project_name)
    filenames_glob = os.path.join(osc_package_path, osc_source_filename_glob)
    filenames = glob.glob(filenames_glob)

    for filename in filenames:
      if not filenames_to_ignore.match(filename):
        logging.info('Removing: {0:s}'.format(filename))

        command = 'osc -q remove {0:s}'.format(os.path.basename(filename))
        exit_code = subprocess.call('(cd {0:s} && {1:s})'.format(
            osc_package_path, command), shell=True)
        if exit_code != 0:
          logging.error('Running: "{0:s}" failed.'.format(command))


class ConfigureMakeOSCBuildHelper(OSCBuildHelper):
  """Helper to build with osc for the openSUSE build service."""

  def Build(self, source_helper_object):
    """Builds the osc package.

    Args:
      source_helper_object (SourceHelper): source helper.

    Returns:
      bool: True if successful, False otherwise.
    """
    source_filename = source_helper_object.Download()
    if not source_filename:
      logging.info('Download of: {0:s} failed'.format(
          source_helper_object.project_name))
      return False

    project_version = source_helper_object.GetProjectVersion()

    logging.info('Preparing osc build of: {0:s}'.format(source_filename))

    if not self._BuildPrepare(source_helper_object):
      return False

    osc_package_path = os.path.join(
        self._OSC_PROJECT, source_helper_object.project_name)

    # osc wants the project filename without the status indication.
    osc_source_filename = '{0:s}-{1!s}.tar.gz'.format(
        source_helper_object.project_name, project_version)

    # Copy the source package to the package directory.
    osc_source_path = os.path.join(osc_package_path, osc_source_filename)
    shutil.copy(source_filename, osc_source_path)

    osc_source_path = os.path.join(
        source_helper_object.project_name, osc_source_filename)
    if not self._OSCAdd(osc_source_path):
      return False

    # Extract the build files from the source package into the package
    # directory.
    spec_filename = '{0:s}.spec'.format(source_helper_object.project_name)

    osc_spec_file_path = os.path.join(osc_package_path, spec_filename)
    spec_file_exists = os.path.exists(osc_spec_file_path)

    command = 'tar xfO {0:s} {1:s}-{2!s}/{3:s} > {3:s}'.format(
        osc_source_filename, source_helper_object.project_name,
        project_version, spec_filename)
    exit_code = subprocess.call('(cd {0:s} && {1:s})'.format(
        osc_package_path, command), shell=True)
    if exit_code != 0:
      logging.error('Running: "{0:s}" failed.'.format(command))
      return False

    if not spec_file_exists:
      osc_spec_file_path = os.path.join(
          source_helper_object.project_name, spec_filename)
      if not self._OSCAdd(osc_spec_file_path):
        return False

    return self._OSCCommit(source_helper_object.project_name)

  def CheckBuildRequired(self, source_helper_object):
    """Checks if a build is required.

    Args:
      source_helper_object (SourceHelper): source helper.

    Returns:
      bool: True if a build is required, False otherwise.
    """
    project_version = source_helper_object.GetProjectVersion()

    osc_source_filename = '{0:s}-{1!s}.tar.gz'.format(
        source_helper_object.project_name, project_version)

    osc_source_path = os.path.join(
        self._OSC_PROJECT, source_helper_object.project_name,
        osc_source_filename)

    return not os.path.exists(osc_source_path)


class SetupPyOSCBuildHelper(OSCBuildHelper):
  """Helper to build with osc for the openSUSE build service."""

  _DOC_FILENAMES = [
      'CHANGES', 'CHANGES.txt', 'CHANGES.TXT',
      'README', 'README.txt', 'README.TXT']

  _LICENSE_FILENAMES = [
      'LICENSE', 'LICENSE.txt', 'LICENSE.TXT']

  def _GetSetupPySpecFilePath(self, source_helper_object, source_directory):
    """Retrieves the path of the setup.py generated .spec file.

    Args:
      source_helper_object (SourceHelper): source helper.
      source_directory (str): name of the source directory.

    Returns:
      str: path of the setup.py generated .spec file.
    """
    if self._project_definition.setup_name:
      setup_name = self._project_definition.setup_name
    else:
      setup_name = source_helper_object.project_name

    spec_filename = '{0:s}.spec'.format(setup_name)

    return os.path.join(source_directory, 'dist', spec_filename)

  def Build(self, source_helper_object):
    """Builds the osc package.

    Args:
      source_helper_object (SourceHelper): source helper.

    Returns:
      bool: True if successful, False otherwise.
    """
    source_filename = source_helper_object.Download()
    if not source_filename:
      logging.info('Download of: {0:s} failed'.format(
          source_helper_object.project_name))
      return False

    logging.info('Preparing osc build of: {0:s}'.format(source_filename))

    if not self._BuildPrepare(source_helper_object):
      return False

    osc_package_path = os.path.join(
        self._OSC_PROJECT, source_helper_object.project_name)

    osc_source_path = os.path.join(osc_package_path, source_filename)
    if not os.path.exists(osc_source_path):
      # Copy the source package to the package directory if needed.
      shutil.copy(source_filename, osc_source_path)

      osc_source_path = os.path.join(
          source_helper_object.project_name, source_filename)
      if not self._OSCAdd(osc_source_path):
        return False

    source_directory = source_helper_object.Create()
    if not source_directory:
      logging.error(
          'Extraction of source package: {0:s} failed'.format(source_filename))
      return False

    spec_file_generator = spec_file.RPMSpecFileGenerator(self._data_path)

    log_file_path = os.path.join('..', self.LOG_FILENAME)
    if not spec_file_generator.GenerateWithSetupPy(
        source_directory, log_file_path):
      return False

    project_name = source_helper_object.project_name
    if project_name.startswith('python-') and project_name != 'python-gflags':
      project_name = project_name[7:]

    # TODO: determine project version.
    project_version = ''

    input_file_path = self._GetSetupPySpecFilePath(
        source_helper_object, source_directory)

    spec_filename = '{0:s}.spec'.format(project_name)
    output_file_path = os.path.join(osc_package_path, spec_filename)

    # Determine if the output file exists before it is generated.
    output_file_exists = os.path.exists(output_file_path)

    if not spec_file_generator.RewriteSetupPyGeneratedFileForOSC(
        self._project_definition, source_directory, source_filename,
        project_name, project_version, input_file_path, output_file_path):
      return False

    if not output_file_exists:
      output_file_path = os.path.join(
          source_helper_object.project_name, spec_filename)
      if not self._OSCAdd(output_file_path):
        return False

    return self._OSCCommit(source_helper_object.project_name)

  def CheckBuildRequired(self, source_helper_object):
    """Checks if a build is required.

    Args:
      source_helper_object (SourceHelper): source helper.

    Returns:
      bool: True if a build is required, False otherwise.
    """
    project_version = source_helper_object.GetProjectVersion()

    osc_source_filename = '{0:s}-{1!s}.tar.gz'.format(
        source_helper_object.project_name, project_version)

    osc_source_path = os.path.join(
        self._OSC_PROJECT, source_helper_object.project_name,
        osc_source_filename)

    return not os.path.exists(osc_source_path)
