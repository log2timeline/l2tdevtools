# -*- coding: utf-8 -*-
"""Dpkg build files generator object implementations."""

import logging
import os
import shutil
import stat
import time

from l2tdevtools import download_helper


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

  _CONTROL_TEMPLATE_HEADER = u'\n'.join([
      u'Source: {package_name:s}',
      u'Section: {section:s}',
      u'Priority: extra',
      u'Maintainer: {upstream_maintainer:s}',
      (u'Build-Depends: debhelper (>= 7){build_depends:s}'),
      u'Standards-Version: 3.9.5',
      u'Homepage: {upstream_homepage:s}',
      u''])

  _CONTROL_TEMPLATE_PACKAGE = u'\n'.join([
      u'',
      u'Package: {package_name:s}',
      u'Architecture: {architecture:s}',
      u'Depends: {depends:s}',
      u'Description: {description_short:s}',
      u' {description_long:s}',
      u''])

  _CONTROL_TEMPLATE_ADDITIONAL_PACKAGE = u'\n'.join([
      u'',
      u'Package: {package_name:s}',
      u'Architecture: {architecture:s}',
      u'Section: {section:s}',
      u'Depends: {depends:s}',
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
      u'\t# Create the {package_library:s} package.',
      u'{install_library:s}',
      u'\t# Create the {package_development:s} package.',
      u'{install_development:s}',
      u'\t# Create the {package_tools:s} package.',
      u'{install_tools:s}',
      u'\t# The {package_debug:s} package is created by dh_strip.',
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
      u'\tdh_strip -p{package_library:s} --dbg-package={package_debug:s}',
      u'endif',
      u'',
      u'.PHONY: override_dh_shlibdeps',
      u'override_dh_shlibdeps:',
      u'\tdh_shlibdeps -L{package_library:s} -l${{CURDIR}}/debian/tmp/usr/lib',
      u'',
      u'.PHONY: override_dh_makeshlibs',
      u'override_dh_makeshlibs:',
      u'\tdh_makeshlibs -X{package_development:s}',
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
      u'{dh_auto_install_override:s}',
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
      self, project_name, project_version, dependency_definition):
    """Initializes the dpkg build files generator.

    Args:
      project_name: the name of the project.
      project_version: the version of the project.
      dependency_definition: the dependency definition object (instance of
                             DependencyDefinition).
    """
    super(DpkgBuildFilesGenerator, self).__init__()
    self._project_name = project_name
    self._project_version = project_version
    self._dependency_definition = dependency_definition

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

    if self._dependency_definition.build_system == u'setup_py':
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
      file_object.write(data.encode('utf-8'))

  def _GenerateCompatFile(self, dpkg_path):
    """Generate the dpkg build compat file.

    Args:
      dpkg_path: the path to the dpkg files.
    """
    filename = os.path.join(dpkg_path, u'compat')
    with open(filename, 'wb') as file_object:
      data = self._COMPAT_TEMPLATE
      file_object.write(data.encode('utf-8'))

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
      # TODO: determine packages.
      packages = [u'libtsk', u'libtsk-dbg', u'libtsk-dev', package_name]
      section = u'libs'

    else:
      package_name = u'python-{0:s}'.format(project_name)
      packages = [package_name]
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
      build_depends.append(u'python')
      build_depends.append(u'python-setuptools')

      if self._dependency_definition.architecture_dependent:
        build_depends.append(u'python-dev')

    build_depends.extend(self._dependency_definition.dpkg_build_dependencies)

    if build_depends:
      build_depends = u', {0:s}'.format(u', '.join(build_depends))
    else:
      build_depends = u''

    filename = os.path.join(dpkg_path, u'control')
    with open(filename, 'wb') as file_object:
      template_values = {
          u'build_depends': build_depends,
          u'package_name': package_name,
          u'section': section,
          u'upstream_maintainer': self._dependency_definition.maintainer,
          u'upstream_homepage': self._dependency_definition.homepage_url}

      data = self._CONTROL_TEMPLATE_HEADER.format(**template_values)
      file_object.write(data.encode('utf-8'))

      for package_index, package_name in enumerate(packages):
        if package_name.endswith(u'-dbg'):
          section = u'debug'
          description_short = u'Debugging symbols for {0:s}'.format(packages[0])
          description_long = description_short
          depends = u'{0:s} (= ${{binary:Version}}), ${{misc:Depends}}'.format(
              packages[0])

        elif package_name.endswith(u'-dev'):
          if package_name.startswith(u'lib'):
            section = u'libdevel'
          else:
            section = u'devel'

          description_short = (
              u'Header files and libraries for developing applications for '
              u'{0:s}').format(packages[0])
          description_long = description_short
          depends = u'{0:s} (= ${{binary:Version}}), ${{misc:Depends}}'.format(
              packages[0])

        else:
          if package_name.startswith(u'lib'):
            section = u'libs'
            # TODO: determine library description.
            description_short = u'Library to support analyzing disk images'
            description_long = description_short

            depends = u'${shlibs:Depends}, ${misc:Depends}'
          else:
            depends = []

            # TODO: put pytsk3 in lookup list.
            if package_name.startswith(u'python-') or package_name == u'pytsk3':
              section = u'python'
            else:
              section = u'tools'
              depends.append(u'{0:s} (= ${{binary:Version}})'.format(
                  packages[0]))

            # description short needs to be a single line.
            description_short = self._dependency_definition.description_short
            description_short = u' '.join(description_short.split(u'\n'))

            # description long needs a space at the start of every line after
            # the first.
            description_long = self._dependency_definition.description_long
            description_long = u'\n '.join(description_long.split(u'\n'))

            depends.extend(self._dependency_definition.dpkg_dependencies)
            depends.append(u'${shlibs:Depends}')
            depends.append(u'${misc:Depends}')
            depends = u', '.join(depends)

        template_values = {
            u'architecture': architecture,
            u'depends': depends,
            u'description_short': description_short,
            u'description_long': description_long,
            u'section': section,
            u'package_name': package_name}

        if package_index == 0:
          data = self._CONTROL_TEMPLATE_PACKAGE.format(**template_values)
        else:
          data = self._CONTROL_TEMPLATE_ADDITIONAL_PACKAGE.format(
              **template_values)

        file_object.write(data.encode('utf-8'))

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

  def _GenerateDocsFile(self, dpkg_path):
    """Generate the dpkg build .docs file.

    Args:
      dpkg_path: the path to the dpkg files.
    """
    if self._dependency_definition.dpkg_name:
      project_name = self._dependency_definition.dpkg_name
    else:
      project_name = self._project_name

    if self._dependency_definition.build_system == u'setup_py':
      project_prefix = u'python-'
    else:
      project_prefix = u''

    # Determine the available doc files.
    doc_files = []
    for filename in self._DOCS_FILENAMES:
      if os.path.exists(filename):
        doc_files.append(filename)

    # TODO: for every package create a docs file.
    filename = os.path.join(
        dpkg_path, u'{0:s}{1:s}.docs'.format(project_prefix, project_name))
    with open(filename, 'wb') as file_object:
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
    build_system = u'--buildsystem=autoconf'

    if self._dependency_definition.patches:
      with_quilt = u'--with quilt'
    else:
      with_quilt = u''

    # TODO: determine configure arguments.
    configure_options = u'--disable-java --with-libewf=no --with-afflib=no'

    # TODO: determine packages and their content.
    package_library = u'libtsk'
    package_debug = u'{0:s}-dbg'.format(package_library)
    package_development = u'{0:s}-dev'.format(package_library)
    package_tools = u'sleuthkit'

    install_library = [
        u'debian/tmp/usr/lib/lib*.so.*.*.*']

    lines = []
    for glob_pattern in install_library:
      lines.append(u'\tdh_install "{0:s}" -p {1:s}'.format(
          glob_pattern, package_library))

    install_library = u'\n'.join(lines)

    install_development = [
        u'debian/tmp/usr/include/tsk/*.h',
        u'debian/tmp/usr/include/tsk/auto/*.h',
        u'debian/tmp/usr/include/tsk/base/*.h',
        u'debian/tmp/usr/include/tsk/fs/*.h',
        u'debian/tmp/usr/include/tsk/hashdb/*.h',
        u'debian/tmp/usr/include/tsk/img/*.h',
        u'debian/tmp/usr/include/tsk/vs/*.h',
        u'debian/tmp/usr/lib/*.a',
        u'debian/tmp/usr/lib/*.la',
        u'debian/tmp/usr/lib/*.so']

    lines = []
    for glob_pattern in install_development:
      lines.append(u'\tdh_install "{0:s}" -p {1:s}'.format(
          glob_pattern, package_development))

    install_development = u'\n'.join(lines)

    install_tools = [
        u'debian/tmp/usr/bin/*',
        u'debian/tmp/usr/share/man/man1/*',
        u'debian/tmp/usr/share/tsk/sorter/*']

    lines = []
    for glob_pattern in install_tools:
      lines.append(u'\tdh_install "{0:s}" -p {1:s}'.format(
          glob_pattern, package_tools))

    install_tools = u'\n'.join(lines)

    template_values = {
        u'build_system': build_system,
        u'configure_options': configure_options,
        u'install_development': install_development,
        u'install_library': install_library,
        u'install_tools': install_tools,
        u'package_debug': package_debug,
        u'package_development': package_development,
        u'package_library': package_library,
        u'package_tools': package_tools,
        u'with_quilt': with_quilt}

    filename = os.path.join(dpkg_path, u'rules')
    with open(filename, 'wb') as file_object:
      data = self._RULES_TEMPLATE_CONFIGURE_MAKE.format(**template_values)
      file_object.write(data.encode('utf-8'))

  def _GenerateSetupPyRulesFile(self, dpkg_path):
    """Generate the dpkg build rules file.

    Args:
      dpkg_path: the path to the dpkg files.
    """
    if self._dependency_definition.dpkg_name:
      project_name = self._dependency_definition.dpkg_name
    else:
      project_name = self._project_name

    package_name = u'python-{0:s}'.format(project_name)

    if self._dependency_definition.patches:
      with_quilt = u'--with quilt'
    else:
      with_quilt = u''

    if not self._dependency_definition.dpkg_manual_install:
      dh_auto_install_override = u''
    else:
      dh_auto_install_override = u'\n'.join([
          u'.PHONY: override_dh_auto_install',
          u'override_dh_auto_install:',
          u'\t# Manually install the Python module files.',
          (u'\tmkdir -p debian/{package_name:s}/usr/lib/python2.7/'
           u'site-packages'),
          (u'\tPYTHONPATH=debian/{package_name:s}/usr/lib/python2.7/'
           u'site-packages python ./setup.py install --prefix debian/'
           u'{package_name:s}}/usr'),
          (u'\tmv debian/{{package_name:s}/usr/lib/python2.7/site-packages '
           u'debian/{package_name:s}/usr/lib/python2.7/dist-packages'),
          u'\t# Remove overrides of existing files.',
          (u'\trm -f debian/{package_name:s}/usr/lib/python2.7/dist-packages/'
           u'easy-install.*'),
          (u'\trm -f debian/{package_name:s}/usr/lib/python2.7/dist-packages/'
           u'site.*'),
          u'\t# Move the Python module files out of the .egg directory.',
          (u'\tmv debian/{package_name:s}/usr/lib/python2.7/dist-packages/'
           u'*.egg/{project_name:s} debian/{package_name:s}/usr/lib/python2.7/'
           u'dist-packages'),
          u'',
          u'']).format({
              u'package_name': package_name,
              u'project_name': project_name})

    template_values = {
        u'dh_auto_install_override': dh_auto_install_override,
        u'with_quilt': with_quilt}

    filename = os.path.join(dpkg_path, u'rules')
    with open(filename, 'wb') as file_object:
      data = self._RULES_TEMPLATE_SETUP_PY.format(**template_values)
      file_object.write(data.encode('utf-8'))

  def _GenerateSourceFormatFile(self, dpkg_path):
    """Generate the dpkg build source/format file.

    Args:
      dpkg_path: the path to the dpkg files.
    """
    filename = os.path.join(dpkg_path, u'source', u'format')
    with open(filename, 'wb') as file_object:
      data = self._SOURCE_FORMAT_TEMPLATE
      file_object.write(data.encode('utf-8'))

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
    self._GenerateDocsFile(dpkg_path)
    self._GenerateRulesFile(dpkg_path)

    os.mkdir(os.path.join(dpkg_path, u'source'))
    self._GenerateSourceFormatFile(dpkg_path)

    if self._dependency_definition.patches:
      download_helper_object = download_helper.DownloadHelper()

      patches_directory = os.path.join(dpkg_path, u'patches')
      os.mkdir(patches_directory)

      current_path = os.getcwd()
      os.chdir(patches_directory)

      patch_filenames = []
      for patch_url in self._dependency_definition.patches:
        filename = download_helper_object.DownloadFile(patch_url)

        _, _, patch_filename = patch_url.rpartition(u'/')
        patch_filenames.append(patch_filename)

      os.chdir(current_path)

      filename = os.path.join(dpkg_path, u'patches', u'series')
      with open(filename, 'wb') as file_object:
        data = u'\n'.join(patch_filenames)
        file_object.write(data.encode('utf-8'))
