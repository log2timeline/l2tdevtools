# -*- coding: utf-8 -*-
"""Writer for Debian packaging (dpkg) files."""

from __future__ import unicode_literals

import io
import os

from l2tdevtools.dependency_writers import interface


class DPKGCompatWriter(interface.DependencyFileWriter):
  """Dpkg compat file writer."""

  PATH = os.path.join('config', 'dpkg', 'compat')

  _FILE_CONTENT = '9\n'

  def Write(self):
    """Writes a dpkg control file."""
    with io.open(self.PATH, 'w', encoding='utf-8') as file_object:
      file_object.write(self._FILE_CONTENT)


class DPKGControlWriter(interface.DependencyFileWriter):
  """Dpkg control file writer."""

  PATH = os.path.join('config', 'dpkg', 'control')

  _PYTHON3_FILE_HEADER = [
      'Source: {project_name:s}',
      'Section: python',
      'Priority: extra',
      'Maintainer: {maintainer:s}',
      'Build-Depends: debhelper (>= 9), dh-python, {build_dependencies:s}',
      'Standards-Version: 4.1.4',
      'X-Python3-Version: >= 3.6',
      'Homepage: {homepage_url:s}',
      '']  # yapf: disable

  _DATA_PACKAGE = [
      'Package: {project_name:s}-data',
      'Architecture: all',
      'Depends: ${{misc:Depends}}',
      'Description: Data files for {name_description:s}',
      '{description_long:s}',
      ''] # yapf: disable

  _PYTHON3_PACKAGE = [
      'Package: python3-{project_name:s}',
      'Architecture: all',
      ('Depends: {python3_dependencies:s}'
       '${{python3:Depends}}, ${{misc:Depends}}'),
      'Description: Python 3 module of {name_description:s}',
      '{description_long:s}',
      '']  # yapf: disable

  _TOOLS_PACKAGE = [
      'Package: {project_name:s}-tools',
      'Architecture: all',
      ('Depends: python3-{project_name:s} (>= ${{binary:Version}}), '
       '${{python3:Depends}}, ${{misc:Depends}}'),
      'Description: Tools of {name_description:s}',
      '{description_long:s}',
      '']  # yapf: disable

  def Write(self):
    """Writes a dpkg control file."""
    file_content = []

    file_content.extend(self._PYTHON3_FILE_HEADER)

    data_dependency = ''
    if os.path.isdir('data'):
      data_dependency = '{0:s}-data (>= ${{binary:Version}})'.format(
          self._project_definition.name)

      file_content.extend(self._DATA_PACKAGE)

    file_content.extend(self._PYTHON3_PACKAGE)

    if (os.path.isdir('scripts') or os.path.isdir('tools') or
        self._project_definition.name == 'timesketch'):
      file_content.extend(self._TOOLS_PACKAGE)

    description_long = self._project_definition.description_long
    description_long = '\n'.join(
        [' {0:s}'.format(line) for line in description_long.split('\n')])

    python3_dependencies = self._dependency_helper.GetDPKGDepends()

    if data_dependency:
      python3_dependencies.insert(0, data_dependency)

    python3_dependencies = ', '.join(python3_dependencies)
    if python3_dependencies:
      python3_dependencies = '{0:s}, '.format(python3_dependencies)

    build_dependencies = ['python3-all (>= 3.6~)', 'python3-setuptools']
    if self._project_definition.name == 'timesketch':
      build_dependencies.insert(0, 'dh-systemd (>= 1.5)')
      build_dependencies.append('python3-pip')

    build_dependencies = ', '.join(build_dependencies)

    template_mappings = {
        'build_dependencies': build_dependencies,
        'description_long': description_long,
        'description_short': self._project_definition.description_short,
        'homepage_url': self._project_definition.homepage_url,
        'maintainer': self._project_definition.maintainer,
        'name_description': self._project_definition.name_description,
        'project_name': self._project_definition.name,
        'python3_dependencies': python3_dependencies}

    file_content = '\n'.join(file_content)
    file_content = file_content.format(**template_mappings)

    with io.open(self.PATH, 'w', encoding='utf-8') as file_object:
      file_object.write(file_content)


class DPKGRulesWriter(interface.DependencyFileWriter):
  """Dpkg rules file writer."""

  PATH = os.path.join('config', 'dpkg', 'rules')

  _FILE_CONTENT = [
      '#!/usr/bin/make -f',
      '',
      '%:',
      '\tdh $@ --buildsystem=pybuild --with=python3',
      '',
      '.PHONY: override_dh_auto_test',
      'override_dh_auto_test:',
      '',
      '']

  def Write(self):
    """Writes a dpkg control file."""
    template_mappings = {
        'project_name': self._project_definition.name}

    file_content = '\n'.join(self._FILE_CONTENT)
    file_content = file_content.format(**template_mappings)

    with io.open(self.PATH, 'w', encoding='utf-8') as file_object:
      file_object.write(file_content)
