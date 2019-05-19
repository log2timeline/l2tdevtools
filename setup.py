#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Installation and deployment script."""

from __future__ import print_function

import glob
import locale
import os
import sys

try:
  from setuptools import find_packages, setup
except ImportError:
  from distutils.core import find_packages, setup

try:
  from distutils.command.bdist_msi import bdist_msi
except ImportError:
  bdist_msi = None

try:
  from distutils.command.bdist_rpm import bdist_rpm
except ImportError:
  bdist_rpm = None

version_tuple = (sys.version_info[0], sys.version_info[1])
if version_tuple[0] not in (2, 3):
  print('Unsupported Python version: {0:s}.'.format(sys.version))
  sys.exit(1)

elif version_tuple[0] == 2 and version_tuple < (2, 7):
  print((
      'Unsupported Python 2 version: {0:s}, version 2.7 or higher '
      'required.').format(sys.version))
  sys.exit(1)

elif version_tuple[0] == 3 and version_tuple < (3, 4):
  print((
      'Unsupported Python 3 version: {0:s}, version 3.4 or higher '
      'required.').format(sys.version))
  sys.exit(1)

# Change PYTHONPATH to include l2tdevtools so that we can get the version.
sys.path.insert(0, '.')

import l2tdevtools  # pylint: disable=wrong-import-position


if not bdist_msi:
  BdistMSICommand = None
else:
  class BdistMSICommand(bdist_msi):
    """Custom handler for the bdist_msi command."""

    def run(self):
      """Builds an MSI."""
      # Command bdist_msi does not support the library version, neither a date
      # as a version but if we suffix it with .1 everything is fine.
      self.distribution.metadata.version += '.1'

      bdist_msi.run(self)


if not bdist_rpm:
  BdistRPMCommand = None
else:
  class BdistRPMCommand(bdist_rpm):
    """Custom handler for the bdist_rpm command."""

    def _make_spec_file(self):
      """Generates the text of an RPM spec file.

      Returns:
        list[str]: lines of the RPM spec file.
      """
      # Note that bdist_rpm can be an old style class.
      if issubclass(BdistRPMCommand, object):
        spec_file = super(BdistRPMCommand, self)._make_spec_file()
      else:
        spec_file = bdist_rpm._make_spec_file(self)

      if sys.version_info[0] < 3:
        python_package = 'python2'
      else:
        python_package = 'python3'

      description = []
      requires = ''
      summary = ''
      in_description = False

      python_spec_file = []
      for line in iter(spec_file):
        if line.startswith('Summary: '):
          summary = line[9:]

        elif line.startswith('BuildRequires: '):
          line = 'BuildRequires: {0:s}-setuptools, {0:s}-devel'.format(
              python_package)

        elif line.startswith('Requires: '):
          requires = line[10:]
          if python_package == 'python3':
            requires = requires.replace('python-', 'python3-')
            requires = requires.replace('python2-', 'python3-')
          continue

        elif line.startswith('%description'):
          in_description = True

        elif line.startswith('python setup.py build'):
          if python_package == 'python3':
            line = '%py3_build'
          else:
            line = '%py2_build'

        elif line.startswith('python setup.py install'):
          if python_package == 'python3':
            line = '%py3_install'
          else:
            line = '%py2_install'

        elif line.startswith('%files'):
          python_spec_file.extend([
              '%package -n %{name}-tools',
              'Requires: {0:s}-l2tdevtools >= %{{version}}'.format(
                  python_package),
              'Summary: Tools for {0:s}'.format(summary),
              '',
              '%description -n %{name}-tools'])

          python_spec_file.extend(description)

          lines = [
              '%files -n %{name}-data',
              '%defattr(644,root,root,755)',
              '%license LICENSE',
              '%doc ACKNOWLEDGEMENTS AUTHORS README',
              '%{_datadir}/%{name}/*',
              '',
              '%files -n {0:s}-%{{name}}'.format(python_package),
              '%defattr(644,root,root,755)',
              '%license LICENSE',
              '%doc ACKNOWLEDGEMENTS AUTHORS README']

          if python_package == 'python3':
            lines.extend([
                '%{python3_sitelib}/l2tdevtools/*.py',
                '%{python3_sitelib}/l2tdevtools/*/*.py',
                '%{python3_sitelib}/l2tdevtools*.egg-info/*',
                '',
                '%exclude %{_prefix}/share/doc/*',
                '%exclude %{python3_sitelib}/l2tdevtools/__pycache__/*',
                '%exclude %{python3_sitelib}/l2tdevtools/*/__pycache__/*'])

          else:
            lines.extend([
                '%{python2_sitelib}/l2tdevtools/*.py',
                '%{python2_sitelib}/l2tdevtools/*/*.py',
                '%{python2_sitelib}/l2tdevtools*.egg-info/*',
                '',
                '%exclude %{_prefix}/share/doc/*',
                '%exclude %{python2_sitelib}/l2tdevtools/*.pyc',
                '%exclude %{python2_sitelib}/l2tdevtools/*.pyo',
                '%exclude %{python2_sitelib}/l2tdevtools/*/*.pyc',
                '%exclude %{python2_sitelib}/l2tdevtools/*/*.pyo'])

          python_spec_file.extend(lines)
          break

        elif line.startswith('%prep'):
          in_description = False

          python_spec_file.extend([
              '%package -n %{name}-data',
              'Summary: Data files for {0:s}'.format(summary),
              '',
              '%description -n %{name}-data'])

          python_spec_file.extend(description)

          python_spec_file.append(
              '%package -n {0:s}-%{{name}}'.format(python_package))
          if python_package == 'python2':
            python_spec_file.extend([
                'Obsoletes: python-l2tdevtools < %{version}',
                'Provides: python-l2tdevtools = %{version}'])
            python_summary = 'Python 2 module of {0:s}'.format(summary)
          else:
            python_summary = 'Python 3 module of {0:s}'.format(summary)

          python_spec_file.extend([
              'Requires: l2tdevtools-data >= %{{version}} {0:s}'.format(
                  requires),
              'Summary: {0:s}'.format(python_summary),
              '',
              '%description -n {0:s}-%{{name}}'.format(python_package)])

          python_spec_file.extend(description)

        elif in_description:
          # Ignore leading white lines in the description.
          if not description and not line:
            continue

          description.append(line)

        python_spec_file.append(line)

      python_spec_file.extend([
          '',
          '%files -n %{name}-tools',
          '%{_bindir}/*.py'])

      return python_spec_file


if version_tuple[0] == 2:
  encoding = sys.stdin.encoding  # pylint: disable=invalid-name

  # Note that sys.stdin.encoding can be None.
  if not encoding:
    encoding = locale.getpreferredencoding()

  # Make sure the default encoding is set correctly otherwise on Python 2
  # setup.py sdist will fail to include filenames with Unicode characters.
  reload(sys)  # pylint: disable=undefined-variable

  sys.setdefaultencoding(encoding)  # pylint: disable=no-member


l2tdevtools_description = (
    'Development tools for the log2timeline projects')

l2tdevtools_long_description = (
    'Development tools for the log2timeline projects.')

setup(
    name='l2tdevtools',
    version=l2tdevtools.__version__,
    description=l2tdevtools_description,
    long_description=l2tdevtools_long_description,
    license='Apache License, Version 2.0',
    url='https://github.com/log2timeline/l2tdevtools',
    maintainer='Log2Timeline maintainers',
    maintainer_email='log2timeline-maintainers@googlegroups.com',
    cmdclass={
        'bdist_msi': BdistMSICommand,
        'bdist_rpm': BdistRPMCommand},
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Console',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
    ],
    packages=find_packages('.', exclude=[
        'tests', 'tests.*', 'tools', 'utils']),
    package_dir={
        'l2tdevtools': 'l2tdevtools'
    },
    scripts=glob.glob(os.path.join('tools', '[a-z]*.py')),
    data_files=[
        ('share/l2tdevtools/data', glob.glob(
            os.path.join('data', '*.ini'))),
        ('share/l2tdevtools/data/dpkg_templates', glob.glob(
            os.path.join('data', 'dpkg_templates', '*'))),
        ('share/l2tdevtools/data/licenses', glob.glob(
            os.path.join('data', 'licenses', '*'))),
        ('share/l2tdevtools/data/msi_prebuild', glob.glob(
            os.path.join('data', 'msi_prebuild', '*'))),
        ('share/l2tdevtools/data/patches', glob.glob(
            os.path.join('data', 'patches', '*'))),
        ('share/l2tdevtools/data/rpm_templates', glob.glob(
            os.path.join('data', 'rpm_templates', '*'))),
        ('share/l2tdevtools/data/templates', glob.glob(
            os.path.join('data', 'templates', '.pylintrc'))),
        ('share/l2tdevtools/data/templates', glob.glob(
            os.path.join('data', 'templates', '*.ini'))),
        ('share/l2tdevtools/data/templates', glob.glob(
            os.path.join('data', 'templates', '*.sh'))),
        ('share/l2tdevtools/data/templates/.travis.yml', glob.glob(
            os.path.join('data', 'templates', '.travis.yml', '*'))),
        ('share/l2tdevtools/data/templates/appveyor.yml', glob.glob(
            os.path.join('data', 'templates', 'appveyor.yml', '*'))),
        ('share/l2tdevtools/data/templates/setup.cfg', glob.glob(
            os.path.join('data', 'templates', 'setup.cfg', '*'))),
        ('share/l2tdevtools/data/templates/setup.py', glob.glob(
            os.path.join('data', 'templates', 'setup.py', '*'))),
        ('share/doc/l2tdevtools', [
            'ACKNOWLEDGEMENTS', 'AUTHORS', 'LICENSE', 'README']),
    ],
)
