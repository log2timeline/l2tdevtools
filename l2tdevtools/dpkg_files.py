# -*- coding: utf-8 -*-
"""Dpkg build files generator object implementations."""

import logging
import os
import shutil
import stat
import time


class DpkgBuildFilesGenerator(object):
  """Class that helps in generating dpkg build files."""

  _EMAIL_ADDRESS = u'Log2Timeline <log2timeline-dev@googlegroups.com>'

  _DOCS_FILENAMES = [
      u'CHANGES', u'CHANGES.txt', u'CHANGES.TXT',
      u'LICENSE', u'LICENSE.txt', u'LICENSE.TXT',
      u'README', u'README.txt', u'README.TXT']

  _CHANGELOG_TEMPLATE = u'\n'.join([
      (u'{project_prefix:s}{project_name:s} ({project_version!s}-1) unstable; '
       u'urgency=low'),
      u'',
      u'  * Auto-generated',
      u'',
      u' -- {maintainer_email_address:s}  {date_time:s}'])

  _COMPAT_TEMPLATE = u'\n'.join([
      u'7'])

  _CONTROL_TEMPLATE = u'\n'.join([
      u'Source: {package_name:s}',
      u'Section: {section:s}',
      u'Priority: extra',
      u'Maintainer: {upstream_maintainer:s}',
      (u'Build-Depends: debhelper (>= 7){build_depends:s}'),
      u'Standards-Version: 3.9.5',
      u'Homepage: {upstream_homepage:s}',
      u'',
      u'Package: {package_name:s}',
      u'Architecture: {architecture:s}',
      u'Depends: {depends:s}',
      u'Description: {description_short:s}',
      u' {description_long:s}',
      u''])

  _CONTROL_TEMPLATE_SETUP_PY = u'\n'.join([
      u'Source: {package_name:s}',
      u'Section: python',
      u'Priority: extra',
      u'Maintainer: {upstream_maintainer:s}',
      (u'Build-Depends: debhelper (>= 7){build_depends:s}'),
      u'Standards-Version: 3.9.5',
      u'X-Python-Version: >= 2.7',
      u'X-Python3-Version: >= 3.4',
      u'Homepage: {upstream_homepage:s}',
      u'',
      u'Package: python-{package_name:s}',
      u'Architecture: {architecture:s}',
      u'Depends: {python_depends:s}'
      u'Description: {description_short:s}',
      u' {description_long:s}',
      u'',
      u'Package: python3-{package_name:s}',
      u'Architecture: {architecture:s}',
      u'Depends: {python3_depends:s}'
      u'Description: {description_short:s}',
      u' {description_long:s}',
      u''])

  _COPYRIGHT_TEMPLATE = u'\n'.join([
      u''])

  _RULES_TEMPLATE_CONFIGURE_MAKE = u'\n'.join([
      u'#!/usr/bin/make -f',
      u'# debian/rules that uses debhelper >= 7.',
      u'',
      u'# Uncomment this to turn on verbose mode.',
      u'#export DH_VERBOSE=1',
      u'',
      u'# This has to be exported to make some magic below work.',
      u'export DH_OPTIONS',
      u'',
      u'%:',
      u'\tdh  $@ {build_system:s} {with_quilt:s}',
      u'',
      u'.PHONY: override_dh_auto_configure',
      u'override_dh_auto_configure:',
      u'\tdh_auto_configure -- {configure_options:s} CFLAGS="-g"',
      u'',
      u'.PHONY: override_dh_auto_test',
      u'override_dh_auto_test:',
      u'',
      u'.PHONY: override_dh_install',
      u'override_dh_install:',
      u'\t# Create the {package_name:s} package.',
      u'{install_package:s}',
      u'# The {package_name:s}-dbg package is created by dh_strip.',
      u'\tdh_install',
      u'',
      u'.PHONY: override_dh_installmenu',
      u'override_dh_installmenu:',
      u'',
      u'.PHONY: override_dh_installmime',
      u'override_dh_installmime:',
      u'',
      u'.PHONY: override_dh_installmodules',
      u'override_dh_installmodules:',
      u'',
      u'.PHONY: override_dh_installlogcheck',
      u'override_dh_installlogcheck:',
      u'',
      u'.PHONY: override_dh_installlogrotate',
      u'override_dh_installlogrotate:',
      u'',
      u'.PHONY: override_dh_installpam',
      u'override_dh_installpam:',
      u'',
      u'.PHONY: override_dh_installppp',
      u'override_dh_installppp:',
      u'',
      u'.PHONY: override_dh_installudev',
      u'override_dh_installudev:',
      u'',
      u'.PHONY: override_dh_installwm',
      u'override_dh_installwm:',
      u'',
      u'.PHONY: override_dh_installxfonts',
      u'override_dh_installxfonts:',
      u'',
      u'.PHONY: override_dh_gconf',
      u'override_dh_gconf:',
      u'',
      u'.PHONY: override_dh_icons',
      u'override_dh_icons:',
      u'',
      u'.PHONY: override_dh_perl',
      u'override_dh_perl:',
      u'',
      u'.PHONY: override_dh_pysupport',
      u'override_dh_pysupport:',
      u'',
      u'.PHONY: override_dh_strip',
      u'override_dh_strip:',
      u'ifeq (,$(filter nostrip,$(DEB_BUILD_OPTIONS)))',
      u'        dh_strip -p{package_name:s} --dbg-package={package_name:s}-dbg',
      u'endif',
      u'',
      u'.PHONY: override_dh_shlibdeps',
      u'override_dh_shlibdeps:',
      u'\tdh_shlibdeps -L{package_name:s} -l${{CURDIR}}/debian/tmp/usr/lib',
      u''])

  # Force the build system to setup.py here in case the package ships
  # a Makefile or equivalent.
  _RULES_TEMPLATE_SETUP_PY = u'\n'.join([
      u'#!/usr/bin/make -f',
      u'# debian/rules that uses debhelper >= 7.',
      u'',
      u'# Uncomment this to turn on verbose mode.',
      u'#export DH_VERBOSE=1',
      u'',
      u'# This has to be exported to make some magic below work.',
      u'export DH_OPTIONS',
      u'',
      u'',
      u'%:',
      u'\tdh  $@ --buildsystem=python_distutils --with=python2 {with_quilt:s}',
      u'',
      u'.PHONY: override_dh_auto_test',
      u'override_dh_auto_test:',
      u'',
      u'.PHONY: override_dh_installmenu',
      u'override_dh_installmenu:',
      u'',
      u'.PHONY: override_dh_installmime',
      u'override_dh_installmime:',
      u'',
      u'.PHONY: override_dh_installmodules',
      u'override_dh_installmodules:',
      u'',
      u'.PHONY: override_dh_installlogcheck',
      u'override_dh_installlogcheck:',
      u'',
      u'.PHONY: override_dh_installlogrotate',
      u'override_dh_installlogrotate:',
      u'',
      u'.PHONY: override_dh_installpam',
      u'override_dh_installpam:',
      u'',
      u'.PHONY: override_dh_installppp',
      u'override_dh_installppp:',
      u'',
      u'.PHONY: override_dh_installudev',
      u'override_dh_installudev:',
      u'',
      u'.PHONY: override_dh_installwm',
      u'override_dh_installwm:',
      u'',
      u'.PHONY: override_dh_installxfonts',
      u'override_dh_installxfonts:',
      u'',
      u'.PHONY: override_dh_gconf',
      u'override_dh_gconf:',
      u'',
      u'.PHONY: override_dh_icons',
      u'override_dh_icons:',
      u'',
      u'.PHONY: override_dh_perl',
      u'override_dh_perl:',
      u'',
      u'.PHONY: override_dh_pysupport',
      u'override_dh_pysupport:',
      u'',
      u'.PHONY: override_dh_python2',
      u'override_dh_python2:',
      u'\tdh_python2 -V 2.7 setup.py',
      u''])

  _RULES_TEMPLATE_SETUP_PY_PYTHON3 = u'\n'.join([
      u'#!/usr/bin/make -f',
      u'# debian/rules that uses debhelper >= 7.',
      u'',
      u'# Uncomment this to turn on verbose mode.',
      u'#export DH_VERBOSE=1',
      u'',
      u'# This has to be exported to make some magic below work.',
      u'export DH_OPTIONS',
      u'',
      u'',
      u'%:',
      (u'\tdh  $@ --buildsystem=python_distutils --with=python2,python3 '
       u'{with_quilt:s}'),
      u'',
      u'.PHONY: override_dh_auto_clean',
      u'override_dh_auto_clean:',
      u'\tdh_auto_clean',
      (u'\trm -rf build {package_name:s}.egg-info/SOURCES.txt '
       u'{package_name:s}.egg-info/PKG-INFO'),
      u'',
      u'.PHONY: override_dh_auto_build',
      u'override_dh_auto_build:',
      u'\tdh_auto_build',
      u'\tset -ex; for python in $(shell py3versions -r); do \\',
      u'\t\t$$python setup.py build; \\',
      u'\tdone;',
      u'',
      u'.PHONY: override_dh_auto_install',
      u'override_dh_auto_install:',
      u'\tdh_auto_install --destdir $(CURDIR)/debian/python-{package_name:s}',
      u'\tset -ex; for python in $(shell py3versions -r); do \\',
      (u'\t\t$$python setup.py install '
       u'--root=$(CURDIR)/debian/python3-{package_name:s} '
       u'--install-layout=deb; \\'),
      u'\tdone;',
      u'',
      u'.PHONY: override_dh_auto_test',
      u'override_dh_auto_test:',
      u'',
      u'.PHONY: override_dh_installmenu',
      u'override_dh_installmenu:',
      u'',
      u'.PHONY: override_dh_installmime',
      u'override_dh_installmime:',
      u'',
      u'.PHONY: override_dh_installmodules',
      u'override_dh_installmodules:',
      u'',
      u'.PHONY: override_dh_installlogcheck',
      u'override_dh_installlogcheck:',
      u'',
      u'.PHONY: override_dh_installlogrotate',
      u'override_dh_installlogrotate:',
      u'',
      u'.PHONY: override_dh_installpam',
      u'override_dh_installpam:',
      u'',
      u'.PHONY: override_dh_installppp',
      u'override_dh_installppp:',
      u'',
      u'.PHONY: override_dh_installudev',
      u'override_dh_installudev:',
      u'',
      u'.PHONY: override_dh_installwm',
      u'override_dh_installwm:',
      u'',
      u'.PHONY: override_dh_installxfonts',
      u'override_dh_installxfonts:',
      u'',
      u'.PHONY: override_dh_gconf',
      u'override_dh_gconf:',
      u'',
      u'.PHONY: override_dh_icons',
      u'override_dh_icons:',
      u'',
      u'.PHONY: override_dh_perl',
      u'override_dh_perl:',
      u'',
      u'.PHONY: override_dh_pysupport',
      u'override_dh_pysupport:',
      u'',
      u'.PHONY: override_dh_python2',
      u'override_dh_python2:',
      u'\tdh_python2 -V 2.7 setup.py',
      u''])

  _SOURCE_FORMAT_TEMPLATE = u'\n'.join([
      u'1.0'])

  def __init__(
      self, project_name, project_version, dependency_definition, data_path):
    """Initializes the dpkg build files generator.

    Args:
      project_name: the name of the project.
      project_version: the version of the project.
      dependency_definition: the dependency definition object (instance of
                             DependencyDefinition).
      data_path: the path to the data directory which contains the patches
                 sub directory.
    """
    super(DpkgBuildFilesGenerator, self).__init__()
    self._data_path = data_path
    self._dependency_definition = dependency_definition
    self._project_name = project_name
    self._project_version = project_version

  def _GenerateChangelogFile(self, dpkg_path):
    """Generate the dpkg build changelog file.

    Args:
      dpkg_path: the path to the dpkg files.
    """
    timezone_minutes, _ = divmod(time.timezone, 60)
    timezone_hours, timezone_minutes = divmod(timezone_minutes, 60)

    # If timezone_hours is -1 {0:02d} will format as -1 instead of -01
    # hence we detect the sign and force a leading zero.
    if timezone_hours < 0:
      timezone_string = u'-{0:02d}{1:02d}'.format(
          -timezone_hours, timezone_minutes)
    else:
      timezone_string = u'+{0:02d}{1:02d}'.format(
          timezone_hours, timezone_minutes)

    date_time_string = u'{0:s} {1:s}'.format(
        time.strftime(u'%a, %d %b %Y %H:%M:%S'), timezone_string)

    if self._dependency_definition.dpkg_name:
      project_name = self._dependency_definition.dpkg_name
    else:
      project_name = self._project_name

    if (not self._dependency_definition.dpkg_name and
        self._dependency_definition.build_system == u'setup_py' and
        not project_name.startswith(u'python-')):
      project_prefix = u'python-'
    else:
      project_prefix = u''

    template_values = {
        u'project_name': project_name,
        u'project_prefix': project_prefix,
        u'project_version': self._project_version,
        u'maintainer_email_address': self._EMAIL_ADDRESS,
        u'date_time': date_time_string}

    filename = os.path.join(dpkg_path, u'changelog')
    with open(filename, 'wb') as file_object:
      data = self._CHANGELOG_TEMPLATE.format(**template_values)
      file_object.write(data.encode(u'utf-8'))

  def _GenerateCompatFile(self, dpkg_path):
    """Generate the dpkg build compat file.

    Args:
      dpkg_path: the path to the dpkg files.
    """
    filename = os.path.join(dpkg_path, u'compat')
    with open(filename, 'wb') as file_object:
      data = self._COMPAT_TEMPLATE
      file_object.write(data.encode(u'utf-8'))

  def _GenerateControlFile(self, dpkg_path):
    """Generate the dpkg build control file.

    Args:
      dpkg_path: the path to the dpkg files.
    """
    if self._dependency_definition.dpkg_name:
      project_name = self._dependency_definition.dpkg_name
    else:
      project_name = self._project_name

    if self._dependency_definition.build_system == u'configure_make':
      package_name = project_name
      section = u'libs'

    elif self._dependency_definition.build_system == u'setup_py':
      if self._dependency_definition.dpkg_name:
        package_name = self._dependency_definition.dpkg_name
      else:
        if not project_name.startswith(u'python-'):
          project_prefix = u'python-'
        else:
          project_prefix = u''

        package_name = u'{0:s}{1:s}'.format(project_prefix, project_name)

      section = u'python'

    if not self._dependency_definition.architecture_dependent:
      architecture = u'all'
    else:
      architecture = u'any'

    build_depends = []
    if self._dependency_definition.patches:
      build_depends.append(u'quilt')

    if self._dependency_definition.build_system == u'configure_make':
      build_depends.append(u'autotools-dev')

    else:
      build_depends.append(u'python-all (>= 2.7~)')
      build_depends.append(u'python-setuptools')

      if self._dependency_definition.architecture_dependent:
        build_depends.append(u'python-dev')

    # TODO: testing.
    if project_name in (u'construct',):
      build_depends.append(u'python3-all (>= 3.4~)')
      build_depends.append(u'python3-setuptools')

      if self._dependency_definition.architecture_dependent:
        build_depends.append(u'python3-dev')

    build_depends.extend(self._dependency_definition.dpkg_build_dependencies)

    if build_depends:
      build_depends = u', {0:s}'.format(u', '.join(build_depends))
    else:
      build_depends = u''

    # description short needs to be a single line.
    description_short = self._dependency_definition.description_short
    description_short = u' '.join(description_short.split(u'\n'))

    # description long needs a space at the start of every line after
    # the first.
    description_long = self._dependency_definition.description_long
    description_long = u'\n '.join(description_long.split(u'\n'))

    depends = []
    python_depends = []
    python3_depends = []

    for dependency in self._dependency_definition.dpkg_dependencies:
      if dependency.startswith(u'python-'):
        python_depends.append(dependency)
        python3_depends.append(u'python-{0:s}'.format(dependency[6:]))
      else:
        depends.append(dependency)

    depends.append(u'${shlibs:Depends}')
    depends.append(u'${misc:Depends}')
    depends = u', '.join(depends)

    python_depends.append(u'${python:Depends}')
    python_depends.append(u'${misc:Depends}')
    python_depends = u', '.join(python_depends)

    python3_depends.append(u'${python3:Depends}')
    python3_depends.append(u'${misc:Depends}')
    python3_depends = u', '.join(python3_depends)

    # TODO: testing.
    if project_name in (u'construct',):
      package_name = project_name

    template_values = {
        u'architecture': architecture,
        u'build_depends': build_depends,
        u'depends': depends,
        u'description_long': description_long,
        u'description_short': description_short,
        u'package_name': package_name,
        u'python_depends': python_depends,
        u'python3_depends': python3_depends,
        u'section': section,
        u'upstream_homepage': self._dependency_definition.homepage_url,
        u'upstream_maintainer': self._dependency_definition.maintainer}

    # TODO: replace the following if with:
    # if self._dependency_definition.build_system == u'setup_py':
    if project_name in (u'construct',):
      control_template = self._CONTROL_TEMPLATE_SETUP_PY
    else:
      control_template = self._CONTROL_TEMPLATE

    if self._dependency_definition.dpkg_template_control:
      template_file_path = os.path.join(
          self._data_path, u'dpkg_templates',
          self._dependency_definition.dpkg_template_control)
      with open(template_file_path, 'rb') as file_object:
        control_template = file_object.read()
        control_template = control_template.decode(u'utf-8')

    filename = os.path.join(dpkg_path, u'control')
    with open(filename, 'wb') as file_object:
      data = control_template.format(**template_values)
      file_object.write(data.encode(u'utf-8'))

  def _GenerateCopyrightFile(self, dpkg_path):
    """Generate the dpkg build copyright file.

    Args:
      dpkg_path: the path to the dpkg files.
    """
    license_file = os.path.dirname(__file__)
    license_file = os.path.dirname(license_file)
    license_file = os.path.join(
        license_file, u'data', u'licenses', u'LICENSE.{0:s}'.format(
            self._project_name))

    filename = os.path.join(dpkg_path, u'copyright')

    if os.path.exists(license_file):
      shutil.copy(license_file, filename)

    else:
      logging.warning(u'Missing license file: {0:s}'.format(license_file))
      with open(filename, 'wb') as file_object:
        file_object.write(u'\n')

  def _GenerateDocsFiles(self, dpkg_path):
    """Generate the dpkg build .docs files.

    Args:
      dpkg_path: the path to the dpkg files.
    """
    if self._dependency_definition.dpkg_name:
      project_name = self._dependency_definition.dpkg_name
    else:
      project_name = self._project_name

    if project_name.startswith(u'python-'):
      project_name = project_name[7:]

    # Determine the available doc files.
    doc_files = []
    for filename in self._DOCS_FILENAMES:
      if os.path.exists(filename):
        doc_files.append(filename)

    package_doc_files = []
    if self._dependency_definition.build_system == u'setup_py':
      package_doc_files.append(u'python-{0:s}.docs'.format(project_name))
      package_doc_files.append(u'python3-{0:s}.docs'.format(project_name))
    else:
      package_doc_files.append(u'{0:s}.docs'.format(project_name))

    for package_doc_file in package_doc_files:
      path = os.path.join(dpkg_path, package_doc_file)
      with open(path, 'wb') as file_object:
        file_object.write(u'\n'.join(doc_files))

  def _GenerateRulesFile(self, dpkg_path):
    """Generate the dpkg build rules file.

    Args:
      dpkg_path: the path to the dpkg files.
    """
    if self._dependency_definition.build_system == u'configure_make':
      self._GenerateConfigureMakeRulesFile(dpkg_path)

    elif self._dependency_definition.build_system == u'setup_py':
      self._GenerateSetupPyRulesFile(dpkg_path)

    filename = os.path.join(dpkg_path, u'rules')
    stat_info = os.stat(filename)
    os.chmod(filename, stat_info.st_mode | stat.S_IEXEC)

  def _GenerateConfigureMakeRulesFile(self, dpkg_path):
    """Generate the dpkg build rules file.

    Args:
      dpkg_path: the path to the dpkg files.
    """
    if self._dependency_definition.dpkg_name:
      package_name = self._dependency_definition.dpkg_name
    else:
      package_name = self._project_name

    build_system = u'--buildsystem=autoconf'

    if self._dependency_definition.patches:
      with_quilt = u'--with quilt'
    else:
      with_quilt = u''

    configure_options = u''
    if self._dependency_definition.dpkg_configure_options:
      configure_options = u' '.join(
          self._dependency_definition.dpkg_configure_options)

    elif self._dependency_definition.configure_options:
      configure_options = u' '.join(
          self._dependency_definition.configure_options)

    install_package = [
        u'debian/tmp/usr/lib/lib*.so.*.*.*']

    lines = []
    for glob_pattern in install_package:
      lines.append(u'\tdh_install "{0:s}" -p {1:s}'.format(
          glob_pattern, install_package))

    install_package = u'\n'.join(lines)

    template_values = {
        u'build_system': build_system,
        u'configure_options': configure_options,
        u'install_package': install_package,
        u'package_name': package_name,
        u'with_quilt': with_quilt}

    rules_template = self._RULES_TEMPLATE_CONFIGURE_MAKE
    if self._dependency_definition.dpkg_template_rules:
      template_file_path = os.path.join(
          self._data_path, u'dpkg_templates',
          self._dependency_definition.dpkg_template_rules)
      with open(template_file_path, 'rb') as file_object:
        rules_template = file_object.read()
        rules_template = rules_template.decode(u'utf-8')

    filename = os.path.join(dpkg_path, u'rules')
    with open(filename, 'wb') as file_object:
      data = rules_template.format(**template_values)
      file_object.write(data.encode(u'utf-8'))

  def _GenerateSetupPyRulesFile(self, dpkg_path):
    """Generate the dpkg build rules file.

    Args:
      dpkg_path: the path to the dpkg files.
    """
    if self._dependency_definition.dpkg_name:
      project_name = self._dependency_definition.dpkg_name
      package_name = self._dependency_definition.dpkg_name
    else:
      project_name = self._project_name
      if not project_name.startswith(u'python-'):
        project_prefix = u'python-'
      else:
        project_prefix = u''

      package_name = u'{0:s}{1:s}'.format(project_prefix, project_name)

    if self._dependency_definition.patches:
      with_quilt = u'--with quilt'
    else:
      with_quilt = u''

    # TODO: testing.
    if project_name in (u'construct',):
      package_name = project_name

    template_values = {
        u'package_name': package_name,
        u'with_quilt': with_quilt}

    filename = os.path.join(dpkg_path, u'rules')
    with open(filename, 'wb') as file_object:
      data = self._RULES_TEMPLATE_SETUP_PY.format(**template_values)
      file_object.write(data.encode(u'utf-8'))

  def _GenerateSourceFormatFile(self, dpkg_path):
    """Generate the dpkg build source/format file.

    Args:
      dpkg_path: the path to the dpkg files.
    """
    filename = os.path.join(dpkg_path, u'source', u'format')
    with open(filename, 'wb') as file_object:
      data = self._SOURCE_FORMAT_TEMPLATE
      file_object.write(data.encode(u'utf-8'))

  def GenerateFiles(self, dpkg_path):
    """Generate the dpkg build files.

    Args:
      dpkg_path: the path to the dpkg files.
    """
    os.mkdir(dpkg_path)
    self._GenerateChangelogFile(dpkg_path)
    self._GenerateCompatFile(dpkg_path)
    self._GenerateControlFile(dpkg_path)
    self._GenerateCopyrightFile(dpkg_path)
    self._GenerateDocsFiles(dpkg_path)
    self._GenerateRulesFile(dpkg_path)

    os.mkdir(os.path.join(dpkg_path, u'source'))
    self._GenerateSourceFormatFile(dpkg_path)

    if self._dependency_definition.patches:
      patches_directory = os.path.join(dpkg_path, u'patches')
      os.mkdir(patches_directory)

      current_path = os.getcwd()
      os.chdir(patches_directory)

      patch_filenames = []
      for patch_filename in self._dependency_definition.patches:
        filename = os.path.join(self._data_path, u'patches', patch_filename)
        if not os.path.exists(filename):
          logging.warning(u'Missing patch file: {0:s}'.format(filename))
          continue

        shutil.copy(filename, patch_filename)
        patch_filenames.append(patch_filename)

      os.chdir(current_path)

      filename = os.path.join(dpkg_path, u'patches', u'series')
      with open(filename, 'wb') as file_object:
        data = u'\n'.join(patch_filenames)
        file_object.write(data.encode(u'utf-8'))
