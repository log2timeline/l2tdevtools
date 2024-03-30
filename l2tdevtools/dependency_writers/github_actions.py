# -*- coding: utf-8 -*-
"""Writer for GitHub actions workflow files."""

import os

from l2tdevtools.dependency_writers import interface


class GitHubActionsTestDockerYmlWriter(interface.DependencyFileWriter):
  """test_docker.yml GitHub actions workflow file writer."""

  _TEMPLATE_FILE = os.path.join(
      'data', 'templates', 'github_actions', 'test_docker.yml')

  PATH = os.path.join('.github', 'workflows', 'test_docker.yml')

  def Write(self):
    """Writes a test_docker.yml GitHub actions workflow file ."""
    dpkg_dependencies = self._GetDPKGPythonDependencies()
    test_dependencies = self._GetDPKGTestDependencies(dpkg_dependencies)
    dpkg_dependencies.extend(test_dependencies)
    dpkg_dependencies.extend([
        'python3', 'python3-build', 'python3-dev', 'python3-pip',
        'python3-wheel'])

    rpm_dependencies = self._GetRPMPythonDependencies()
    test_dependencies = self._GetRPMTestDependencies(rpm_dependencies)
    rpm_dependencies.extend(test_dependencies)
    rpm_dependencies.extend([
        'python3', 'python3-build', 'python3-devel', 'python3-wheel'])

    template_mappings = {
        'dpkg_dependencies': ' '.join(sorted(set(dpkg_dependencies))),
        'rpm_dependencies': ' '.join(sorted(set(rpm_dependencies)))}

    template_file = os.path.join(self._l2tdevtools_path, self._TEMPLATE_FILE)
    file_content = self._GenerateFromTemplate(template_file, template_mappings)

    with open(self.PATH, 'w', encoding='utf-8') as file_object:
      file_object.write(file_content)


class GitHubActionsTestDocsYmlWriter(interface.DependencyFileWriter):
  """test_docs.yml GitHub actions workflow file writer."""

  _TEMPLATE_FILE = os.path.join(
      'data', 'templates', 'github_actions', 'test_docs.yml')

  PATH = os.path.join('.github', 'workflows', 'test_docs.yml')

  def Write(self):
    """Writes a test_docs.yml GitHub actions workflow file ."""
    dpkg_dependencies = self._GetDPKGPythonDependencies()
    test_dependencies = self._GetDPKGTestDependencies(dpkg_dependencies)
    dpkg_dependencies.extend(test_dependencies)
    dpkg_dependencies.append('python3-pip')

    dpkg_dev_dependencies = self._GetDPKGDevDependencies()

    template_mappings = {
        'dpkg_dependencies': ' '.join(sorted(set(dpkg_dependencies))),
        'dpkg_dev_dependencies': ' '.join(sorted(set(dpkg_dev_dependencies)))}

    template_file = os.path.join(self._l2tdevtools_path, self._TEMPLATE_FILE)
    file_content = self._GenerateFromTemplate(template_file, template_mappings)

    with open(self.PATH, 'w', encoding='utf-8') as file_object:
      file_object.write(file_content)


class GitHubActionsTestToxYmlWriter(interface.DependencyFileWriter):
  """test_tox.yml GitHub actions workflow file writer."""

  _TEMPLATE_FILE = os.path.join(
      'data', 'templates', 'github_actions', 'test_tox.yml')

  PATH = os.path.join('.github', 'workflows', 'test_tox.yml')

  def Write(self):
    """Writes a test_tox.yml GitHub actions workflow file ."""
    dpkg_dependencies = self._GetDPKGPythonDependencies()
    test_dependencies = self._GetDPKGTestDependencies(dpkg_dependencies)
    dpkg_dependencies.extend(test_dependencies)
    dpkg_dependencies.append('python3-pip')

    dpkg_dev_dependencies = self._GetDPKGDevDependencies()

    template_mappings = {
        'dpkg_dependencies': ' '.join(sorted(set(dpkg_dependencies))),
        'dpkg_dev_dependencies': ' '.join(sorted(set(dpkg_dev_dependencies)))}

    template_file = os.path.join(self._l2tdevtools_path, self._TEMPLATE_FILE)
    file_content = self._GenerateFromTemplate(template_file, template_mappings)

    with open(self.PATH, 'w', encoding='utf-8') as file_object:
      file_object.write(file_content)
