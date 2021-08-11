#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Script to retrieve GitHub project statistics."""

import argparse
import configparser
import datetime
import json
import logging
import os
import sys
import time

import urllib.error as urllib_error
from urllib.request import urlopen


class StatsDefinitionReader(object):
  """Class that implements a stats definition reader."""

  def _GetConfigValue(self, config_parser, section_name, value_name):
    """Retrieves a value from the config parser.

    Args:
      config_parser (ConfigParser): configuration parser.
      section_name (str): name of the section that contains the value.
      value_name (str): name of the value.

    Returns:
      object: value or None if the value does not exists.
    """
    try:
      return config_parser.get(section_name, value_name)
    except configparser.NoOptionError:
      return None

  def ReadProjectsPerOrganization(self, file_object):
    """Reads the projects per organization.

    Args:
      file_object (file): file-like object to read from.

    Returns:
      dict[str, list[str]]: organization names with corresponding project names.
    """
    config_parser = configparser.ConfigParser(interpolation=None)
    config_parser.read_file(file_object)

    projects_per_organization = {}
    for option_name in config_parser.options('organizations'):
      project_names = self._GetConfigValue(
          config_parser, 'organizations', option_name)

      if project_names is None:
        project_names = []
      elif isinstance(project_names, str):
        project_names = project_names.split(',')

      projects_per_organization[option_name] = project_names

    return projects_per_organization

  def ReadUserMappings(self, file_object):
    """Reads the username mappings.

    Args:
      file_object (file): file-like object to read from.

    Returns:
      dict[str, str]: user names with corresponding email address.
    """
    config_parser = configparser.ConfigParser(interpolation=None)
    config_parser.read_file(file_object)

    user_mappings = {}
    for option_name in config_parser.options('user_mappings'):
      user_mapping = self._GetConfigValue(
          config_parser, 'user_mappings', option_name)

      option_name = option_name.lower()
      user_mappings[option_name] = user_mapping.lower()

    return user_mappings

  def ReadUsernames(self, file_object):
    """Reads the usernames.

    Args:
      file_object (file): file-like object to read from.

    Returns:
      dict[str, str]: user names with corresponding email address.
    """
    config_parser = configparser.ConfigParser(interpolation=None)
    config_parser.read_file(file_object)

    usernames = {}
    for option_name in config_parser.options('usernames'):
      email_address = self._GetConfigValue(
          config_parser, 'usernames', option_name)

      usernames[option_name] = email_address

    return usernames


class DownloadHelper(object):
  """Class that defines a download helper."""

  def _DownloadPageContent(self, download_url):
    """Downloads the page content from the URL.

    Args:
      download_url (str): URL where to download the page content.

    Returns:
      tuple[bytes, TODO]: page content and response headers if successful or
          None otherwise.
    """
    if not download_url:
      return None, None

    try:
      url_object = urlopen(download_url)
    except urllib_error.URLError as exception:
      logging.warning(
          'Unable to download URL: {0:s} with error: {1!s}'.format(
              download_url, exception))
      return None, None

    if url_object.code != 200:
      return None, None

    return url_object.read(), url_object.info()


class GithubContributionsHelper(DownloadHelper):
  """Class that defines a GitHub contributions helper."""

  def _ListContributionsForProject(
      self, organization, project_name, output_writer):
    """Lists the contributions of a specific project.

    Args:
      organization (str): name of the organization.
      project_name (str): name of the project.
      output_writer (OutputWriter): output writer.
    """
    download_url = (
        'https://api.github.com/repos/{0:s}/{1:s}/stats/contributors').format(
            organization, project_name)

    contributors_data, response = self._DownloadPageContent(download_url)
    if not contributors_data:
      return

    # TODO: check if response is not None
    _ = response

    contributors_json = json.loads(contributors_data)
    self._WriteContributions(project_name, contributors_json, output_writer)

  def _ListPullRequestsForProject(
      self, organization, project_name, output_writer):
    """Lists the pull requests of a specific project.

    Args:
      organization (str): name of the organization.
      project_name (str): name of the project.
      output_writer (OutputWriter): output writer.
    """
    download_url = (
        'https://api.github.com/repos/{0:s}/{1:s}/pulls?state=all').format(
            organization, project_name)

    pulls_data, response = self._DownloadPageContent(download_url)
    if not pulls_data:
      return

    # TODO: check if response is not None
    _ = response

    pulls_json = json.loads(pulls_data)
    self._WritePullRequests(project_name, pulls_json, output_writer)

  def _WriteContributions(self, project_name, contributors_json, output_writer):
    """Writes the contributions to the output writer.

    Args:
      project_name (str): name of the project.
      contributors_json (list[object]): JSON formatted contributors objects.
      output_writer (OutputWriter): output writer.
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
    for contributions_per_author_json in contributors_json:
      author_json = contributions_per_author_json.get("author", None)
      if not author_json:
        logging.error('Missing author JSON dictionary.')
        continue

      weeks_json = contributions_per_author_json.get("weeks", None)
      if not weeks_json:
        logging.error('Missing weeks JSON list.')
        continue

      login_name = author_json.get("login", None)
      if not login_name:
        logging.error('Missing login name JSON value.')
        continue

      # TODO: map login name to username

      for week_json in weeks_json:
        number_of_lines_added = week_json.get('a', 0)
        number_of_contributions = week_json.get('c', 0)
        number_of_lines_deleted = week_json.get('d', 0)

        if (not number_of_lines_added and not number_of_contributions and
            not number_of_lines_deleted):
          continue

        week_timestamp = week_json.get('w', None)
        if not week_timestamp:
          logging.error('Missing week timestamp JSON value.')
          continue

        time_elements = time.gmtime(week_timestamp)
        year = time.strftime('%Y', time_elements)
        week_number = time.strftime('%U', time_elements)

        if week_number not in contributions_per_week:
          contributions_per_week[week_number] = {}

        contributions_per_week[week_number][login_name] = (
            number_of_contributions, number_of_lines_added,
            number_of_lines_deleted)

        output_writer.WriteContribution(
            year, week_number, login_name, project_name,
            number_of_contributions, number_of_lines_added,
            number_of_lines_deleted)

  def _WritePullRequests(self, project_name, pulls_json, output_writer):
    """Writes the pull requests to the output writer.

    Args:
      project_name (str): name of the project.
      pulls_json (list[object]): JSON formatted pull objects.
      output_writer (OutputWriter): output writer.
    """
    # https://developer.github.com/v3/pulls/#list-pull-requests
    # [{
    #  "created_at": creation date and time of the CL.
    #  "state": state of the CL.
    #  "title": string containing the CL description.
    #  "user": {
    #    "login": github username.
    #   }, ...]
    #  ...
    # }, ...]

  def ListContributions(self, projects_per_organization, output_writer):
    """Lists the contributions of projects.

    Args:
      projects_per_organization (dict[str, list[str]]): organization names
          with corresponding projects names.
      output_writer (OutputWriter): output writer.
    """
    for organization, projects in iter(projects_per_organization.items()):
      for project_name in projects:
        self._ListContributionsForProject(
            organization, project_name, output_writer)

  def ListPullRequests(self, projects_per_organization, output_writer):
    """Lists the pull requests of projects.

    Args:
      projects_per_organization (dict[str, list[str]]): organization names
          with corresponding projects names.
      output_writer (OutputWriter): output writer.
    """
    for organization, projects in iter(projects_per_organization.items()):
      for project_name in projects:
        self._ListPullRequestsForProject(
            organization, project_name, output_writer)


class StdoutWriter(object):
  """Class that defines a stdout output writer."""

  def __init__(self, user_mappings, output_format='csv'):
    """Initializes a stdout output writer.

    Args:
      user_mappings (dict[str, str]): mapping between GitHub username and
          another username.
      output_format (Optional[str]): output format.
    """
    super(StdoutWriter, self).__init__()
    self._header_written = False
    self._output_format = output_format
    self._user_mappings = user_mappings

  def Open(self):
    """Opens the output writer object.

    Returns:
      bool: True if successful or False if not.
    """
    return True

  def Close(self):
    """Closes the output writer object."""
    return

  def Write(self, data):
    """Writes the data to stdout (without the default trailing newline).

    Args:
      data (str): data to write.
    """
    print(data, end='')

  def WriteContribution(
      self, year, week_number, login_name, project_name,
      number_of_contributions, number_of_lines_added, number_of_lines_deleted):
    """Writes a contribution to stdout.

    Args:
      year (int): year of the contribution.
      week_number (int): week number of the contribution.
      login_name (str): log-in name.
      project_name (str): project name.
      number_of_contributions (int): number of contributed CLs.
      number_of_lines_added (int): total number of lines added.
      number_of_lines_deleted (int): total number of lines deleted.
    """
    username = login_name

    if self._user_mappings:
      username = username.lower()
      username = self._user_mappings.get(username, None)
      # TODO: add flag to control this behavior.
      if not username:
        # Skip login names without a username mapping.
        return

    if self._output_format == 'csv':
      if not self._header_written:
        self.Write(
            'year\tweek number\tlogin name\tproject\tnumber of contributions\t'
            'number lines added\tnumber lines deleted\n')

        self._header_written = True

      self.Write('{0:s}\t{1:s}\t{2:s}\t{3:s}\t{4:d}\t{5:d}\t{6:d}\n'.format(
          year, week_number, username, project_name, number_of_contributions,
          number_of_lines_added, number_of_lines_deleted))

    elif self._output_format == 'tilde':
      date_time_string = '{0:s}-W{1:s}-0'.format(year, week_number)
      date_time = datetime.datetime.strptime(date_time_string, '%Y-W%W-%w')
      date_time_string = date_time.isoformat()

      # TODO: add description.
      self.Write((
          '{0:s} [github] ~ author:{1:s} ~ project:{2:s} ~ '
          'number_of_cls:{3:d} ~ delta_added:{4:d} ~ delta_deleted:{5:d} '
          '~ py:{4:d} ~ file_type:py ~ op_type:ADD ~\n').format(
              date_time_string, username, project_name, number_of_contributions,
              number_of_lines_added, number_of_lines_deleted))

  def WriteReview(
      self, creation_time, created_by, issue_number, description, reviewers,
      status):
    """Writes a review to stdout.

    Args:
      creation_time (str): creation date and time.
      created_by (str): created by.
      issue_number (int): code review issue number.
      description (str): description.
      reviewers (str): reviewers.
      status (str): status.
    """
    if self._output_format == 'csv':
      if not self._header_written:
        self.Write(
            'creation time\tcreated by\tissue number\tdescription\treviewers\t'
            'status\n')

        self._header_written = True

      self.Write('{0:s}\t{1:s}\t{2:d}\t{3:s}\t{4:s}\t{5:s}\n'.format(
          creation_time, created_by, issue_number, description, reviewers,
          status))


def Main():
  """The main program function.

  Returns:
    bool: True if successful or False if not.
  """
  statistics_types = frozenset(['contributions'])

  argument_parser = argparse.ArgumentParser(description=(
      'Generates an overview of project statistics of github projects.'))

  argument_parser.add_argument(
      '-c', '--config', dest='config_path', action='store',
      metavar='PATH', default=None, help=(
          'path of the directory containing the statistics configuration '
          'files e.g. stats.ini.'))

  argument_parser.add_argument(
      '-f', '--format', dest='output_format', action='store',
      metavar='FORMAT', choices=['csv', 'tilde'], default='csv',
      help='output format.')

  argument_parser.add_argument(
      'statistics_type', action='store', metavar='TYPE',
      choices=sorted(statistics_types), default=None,
      help='The statistics type.')

  options = argument_parser.parse_args()

  if not options.statistics_type:
    print('Statistics type missing.')
    print('')
    argument_parser.print_help()
    print('')
    return False

  config_path = options.config_path
  if not config_path:
    config_path = os.path.dirname(__file__)
    config_path = os.path.dirname(config_path)
    config_path = os.path.join(config_path, 'data')

  stats_file = os.path.join(config_path, 'stats.ini')
  if not os.path.exists(stats_file):
    print('No such config file: {0:s}.'.format(stats_file))
    print('')
    return False

  stats_definition_reader = StatsDefinitionReader()

  user_mappings = {}
  with open(stats_file) as file_object:
    user_mappings = stats_definition_reader.ReadUserMappings(file_object)

  output_writer = StdoutWriter(
      user_mappings, output_format=options.output_format)

  if not output_writer.Open():
    print('Unable to open output writer.')
    print('')
    return False

  if options.statistics_type == 'contributions':
    projects_per_organization = {}
    with open(stats_file) as file_object:
      stats_definition_reader = StatsDefinitionReader()
      projects_per_organization = (
          stats_definition_reader.ReadProjectsPerOrganization(file_object))

    contributions_helper = GithubContributionsHelper()
    contributions_helper.ListContributions(
        projects_per_organization, output_writer)

  # TODO: add support for pull requests
  # TODO: add support for more granular CL information

  return True


if __name__ == '__main__':
  if not Main():
    sys.exit(1)
  else:
    sys.exit(0)
