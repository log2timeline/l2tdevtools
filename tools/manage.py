#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Script to manage the GIFT launchpad PPA and l2tbinaries."""

from __future__ import print_function
import argparse
import logging
import os
import sys

from l2tdevtools import download_helper


class LaunchpadPPAManager(object):
  """Defines a Launchpad PPA manager object."""

  _LAUNCHPAD_URL = (
      u'http://ppa.launchpad.net/{name:s}/{track:s}/ubuntu/dists'
      u'/trusty/main/source/Sources')

  def __init__(self, name):
    """Initializes the Launchpad PPA manager object.

    Args:
      name: a string containing the name of the PPA.
    """
    super(LaunchpadPPAManager, self).__init__()
    self._download_helper = download_helper.DownloadHelper()
    self._name = name

  def CopyPackages(self):
    # TODO: implement:
    # send post to https://launchpad.net/~gift/+archive/ubuntu/testing
    #              /+copy-packages
    return

  def GetPackages(self, track):
    """Retrieves a list of packages of a specific PPA track.

    Args:
      track: a string containing the PPA track name.

    Returns:
      A dictionary object containing the project names as keys and
      versions as values or None if the projects cannot be determined.
    """
    kwargs = {
        u'name': self._name,
        u'track': track}
    download_url = self._LAUNCHPAD_URL.format(**kwargs)

    ppa_sources = self._download_helper.DownloadPageContent(download_url)
    if not ppa_sources:
      logging.error(u'Unable to retrieve PPA sources list.')
      return

    try:
      ppa_sources = ppa_sources.decode(u'utf-8')
    except UnicodeDecodeError as exception:
      logging.error(
          u'Unable to decode PPA sources list with error: {0:s}'.format(
              exception))
      return

    projects = {}
    for line in ppa_sources.split(u'\n'):
      if line.startswith(u'Package: '):
        _, _, project = line.rpartition(u'Package: ')

      elif line.startswith(u'Version: '):
        _, _, version = line.rpartition(u'Version: ')
        version, _, _ = version.rpartition(u'-')

        projects[project] = version

    return projects


class OpenSuseBuildServiceManager(object):
  """Defines an OpenSuse build service manager object."""

  # http://download.opensuse.org/repositories/home:/joachimmetz:/testing/
  # Fedora_22/src/

  # TODO: update
  # ocs checkout home:joachimmetz:testing
  # cd home:joachimmetz:testing
  #
  # osc meta pkg -F - home:joachimmetz:testing libevt << EOT
  # <package name="libevt" project="home:joachimmetz:testing">
  #   <title>{title:s}</title>
  #   <description>{description:s}</description>
  # </package>
  # EOT
  #
  # osc up
  #
  # cp libevt-alpha-20151206.tar.gz libevt/libevt-20151206.tar.gz
  # tar xfO libevt/libevt-20151206.tar.gz libevt-20151206/libevt.spec
  # > libevt/libevt.spec
  #
  # osc add libevt/libevt*
  # osc commit -n


class BinariesManager(object):
  """Defines the binaries manager."""

  def __init__(self):
    """Initializes the binaries manager object."""
    super(BinariesManager, self).__init__()
    self._launchpad_ppa_manager = LaunchpadPPAManager(u'gift')

  def _ComparePackages(self, reference_packages, packages):
    """Compares the packages.

    Args:
      reference_packages: a dictionary containing the reference package names
                          and versions.
      packages: a dictionary containing the package names and versions.

    Returns:
      A tuple containing a dictionary of the new packages, those packages that
      are present in the reference packages but not in the packages, and new
      version, those packages that have a newer version in the reference
      packages.
    """
    new_packages = {}
    new_versions = {}
    for name, version in iter(reference_packages.items()):
      if name not in packages:
        new_packages[name] = version
      elif version != packages[name]:
        new_versions[name] = version

    return new_packages, new_versions

  def CompareDirectoryWithReleaseTrack(self, reference_directory, track):
    """Compares a directory containing dpkg packages with a release track.

    Args:
      reference_directory: a string containing the path of the reference
                           directory that contains dpkg source packages.
      track: a string containing the name of the track.

    Returns:
      A tuple containing a dictionary of the new packages, those packages that
      are present in the reference directory but not in the track, and new
      version, those packages that have a newer version in the reference
      directory.
    """
    reference_packages = {}
    for directory_entry in os.listdir(reference_directory):
      # The directory contains various files and we are only interested
      # in the source dpkg packges that use the naming convention:
      # package_version-#ppa1~trusty_source.changes
      if not directory_entry.endswith(u'ppa1~trusty_source.changes'):
        continue

      name, _, _ = directory_entry.rpartition(u'-')
      name, _, version = name.rpartition(u'_')

      reference_packages[name] = version

    packages = self._launchpad_ppa_manager.GetPackages(track)
    return self._ComparePackages(reference_packages, packages)

  def CompareReleaseTracks(self, reference_track, track):
    """Compares two release tracks.

    Args:
      reference_track: a string containing the name of the reference track.
      track: a string containing the name of the track.

    Returns:
      A tuple containing a dictionary of the new packages, those packages that
      are present in the reference track but not in the track, and new
      version, those packages that have a newer version in the reference track.
    """
    reference_packages = self._launchpad_ppa_manager.GetPackages(
        reference_track)
    packages = self._launchpad_ppa_manager.GetPackages(track)

    return self._ComparePackages(reference_packages, packages)


def Main():
  actions = frozenset([
      u'launchpad-diff-dev', u'launchpad-diff-stable',
      u'launchpad-diff-testing', u'osb-update-testing'])

  argument_parser = argparse.ArgumentParser(description=(
      u'Manages the GIFT launchpad PPA and l2tbinaries.'))

  argument_parser.add_argument(
      u'action', choices=sorted(actions), action=u'store',
      metavar=u'ACTION', default=None, help=u'The action.')

  argument_parser.add_argument(
      u'--build-directory', u'--build_directory', action=u'store',
      metavar=u'DIRECTORY', dest=u'build_directory', type=str,
      default=u'build', help=u'The location of the the build directory.')

  options = argument_parser.parse_args()

  if not options.action:
    print(u'Missing action.')
    print(u'')
    argument_parser.print_help()
    print(u'')
    return False

  # TODO: add action to upload files to PPA.
  # TODO: add action to copy files between PPA tracks.
  # TODO: add l2tbinaries support.
  # TODO: add pypi support.

  binaries_manager = BinariesManager()

  if options.action.startswith(u'launchpad-diff-'):
    if options.action.endswith(u'-testing'):
      reference_directory = options.build_directory
      track = u'testing'

      new_packages, new_versions = (
          binaries_manager.CompareDirectoryWithReleaseTrack(
              reference_directory, track))

      diff_header = (
          u'Difference between: {0:s} and release track: {1:s}'.format(
              reference_directory, track))

    else:
      if options.action.endswith(u'-dev'):
        reference_track = u'testing'
        track = u'dev'
      else:
        reference_track = u'dev'
        track = u'stable'

      new_packages, new_versions = binaries_manager.CompareReleaseTracks(
          reference_track, track)

      diff_header = (
          u'Difference between release tracks: {0:s} and {1:s}'.format(
              reference_track, track))

  # elif options.action.startswith(u'osb-diff-'):

  if u'-diff-' in options.action:
    print(diff_header)
    print(u'')

    print(u'New packages:')
    for package in sorted(new_packages.keys()):
      print(u'  {0:s}'.format(package))
    print(u'')

    print(u'New versions:')
    for package in sorted(new_versions.keys()):
      print(u'  {0:s}'.format(package))
    print(u'')

  return True


if __name__ == '__main__':
  if not Main():
    sys.exit(1)
  else:
    sys.exit(0)
