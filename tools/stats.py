#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Script to retrieve project statistics."""

from __future__ import print_function
import argparse
import json
import logging
import sys
import time

# pylint: disable=import-error
# pylint: disable=no-name-in-module
if sys.version_info[0] < 3:
  # Keep urllib2 here since we this code should be able to be used
  # by a default Python set up.
  import urllib2 as urllib_error
  from urllib2 import urlopen
else:
  import urllib.error as urllib_error
  from urllib.request import urlopen


class GithubContributionsHelper(object):
  """Class that defines a github contributions helper."""

  def __init__(self, organization):
    """Initialize the contributions helper object.

    Args:
      organization: a string containing the name of the organization.
    """
    super(GithubContributionsHelper, self).__init__()
    self._organization = organization

  def _DownloadPageContent(self, download_url):
    """Downloads the page content from the URL.

    Args:
      download_url: the URL where to download the page content.

    Returns:
      A tuple of a binary string containing the page content and
      TODO conaining the response headers if successful, None otherwise.
    """
    if not download_url:
      return None, None

    try:
      url_object = urlopen(download_url)
    except urllib_error.URLError as exception:
      logging.warning(
          u'Unable to download URL: {0:s} with error: {1:s}'.format(
              download_url, exception))
      return None, None

    if url_object.code != 200:
      return None, None

    return url_object.read(), url_object.info()

  def _ListContributionsForProject(self, project_name, output_writer):
    """Lists the contributionss of a specific project.

    Args:
      project_name: a string containing the name of the project.
      output_writer: an output writer object (instance of OutputWriter).
    """
    download_url = (
        u'https://api.github.com/repos/{0:s}/{1:s}/stats/contributors').format(
            self._organization, project_name)

    contributions_data, response = self._DownloadPageContent(download_url)
    if not contributions_data:
      return

    contributions_json = json.loads(contributions_data)
    self._WriteContribution(project_name, contributions_json, output_writer)

    # TODO: check if response is not None

  def _WriteContribution(self, project_name, contributions_json, output_writer):
    """Writes the contributions to the output writer.

    Args:
      project_name: a string containing the name of the project.
      contributions_json: a JSON contributions object (instance of TODO).
      output_writer: an output writer object (instance of OutputWriter).
    """
    # https://developer.github.com/v3/repos/statistics/
    # [{
    #  "author": {
    #     "login": string containing the login name,
    #     ...
    #   }
    #   "weeks": [{
    #     "a": integer containing the number of lines added,
    #     "c": integer containing the number of contributions,
    #     "d": integer containing the number of lines deleted,
    #     "w": integer containing a POSIX timestamp of the start of the week,
    #   }, ...],
    # }, ...]

    contributions_per_week = {}
    for contributions_per_author_json in contributions_json:
      author_json = contributions_per_author_json.get("author", None)
      if not author_json:
        logging.error(u'Missing author JSON dictionary.')
        continue

      weeks_json = contributions_per_author_json.get("weeks", None)
      if not weeks_json:
        logging.error(u'Missing weeks JSON list.')
        continue

      login_name = author_json.get("login", None)
      if not login_name:
        logging.error(u'Missing login name JSON value.')
        continue

      for week_json in weeks_json:
        number_of_lines_added = week_json.get(u'a', 0)
        number_of_contributions = week_json.get(u'c', 0)
        number_of_lines_deleted = week_json.get(u'd', 0)

        if (not number_of_lines_added and not number_of_contributions and
            not number_of_lines_deleted):
          continue

        week_timestamp = week_json.get(u'w', None)
        if not week_timestamp:
          logging.error(u'Missing week timestamp JSON value.')
          continue

        time_elements = time.gmtime(week_timestamp)
        year = time.strftime(u'%Y', time_elements)
        week_number = time.strftime(u'%U', time_elements)

        if week_number not in contributions_per_week:
          contributions_per_week[week_number] = {}

        contributions_per_week[week_number][login_name] = (
            number_of_contributions, number_of_lines_added,
            number_of_lines_deleted)

        output_line = u'{0:s}\t{1:s}\t{2:s}\t{3:s}\t{4:d}\t{5:d}\t{6:d}\n'.format(
            year, week_number, login_name, project_name, number_of_contributions,
            number_of_lines_added, number_of_lines_deleted)

        output_writer.Write(output_line.decode(u'utf-8'))

  def ListContributions(self, project_names, output_writer):
    """Lists the contributions of projects.

    Args:
      project_names: a list of strings containing the names of the projects.
      output_writer: an output writer object (instance of OutputWriter).
    """
    output_line = (
        u'year\tweek number\tlogin name\tproject\tnumber of contributions\t'
        u'number lines added\tnumber lines deleted\n')
    output_writer.Write(output_line.decode(u'utf-8'))

    for project_name in project_names:
      self._ListContributionsForProject(project_name, output_writer)


class StdoutWriter(object):
  """Class that defines a stdout output writer."""

  def __init__(self):
    """Initializes an output writer object."""
    super(StdoutWriter, self).__init__()

  def Open(self):
    """Opens the output writer object.

    Returns:
      A boolean containing True if successful or False if not.
    """
    return True

  def Close(self):
    """Closes the output writer object."""
    return

  def Write(self, data):
    """Writes the data to stdout (without the default trailing newline).

    Args:
      data: the data to write.
    """
    print(data, end=u'')


def Main():
  """The main program function.

  Returns:
    A boolean containing True if successful or False if not.
  """
  argument_parser = argparse.ArgumentParser(description=(
      u'Generates an overview of project statistics of the log2timeline '
      u'projects.'))

  options = argument_parser.parse_args()

  output_writer = StdoutWriter()

  if not output_writer.Open():
    print(u'Unable to open output writer.')
    print(u'')
    return False

  organization = u'log2timeline'
  project_names = [u'dfdatetime', u'dfvfs', u'dfwinreg', u'plaso']

  contributions_helper = GithubContributionsHelper(organization)
  contributions_helper.ListContributions(project_names, output_writer)

  return True


if __name__ == '__main__':
  if not Main():
    sys.exit(1)
  else:
    sys.exit(0)
