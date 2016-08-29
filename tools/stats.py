#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Script to retrieve github project statistics."""

from __future__ import print_function
import argparse
import json
import logging
import os
import sys
import time

try:
  import ConfigParser as configparser
except ImportError:
  import configparser  # pylint: disable=import-error

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
      return config_parser.get(section_name, value_name).decode('utf-8')
    except configparser.NoOptionError:
      return

  def ReadProjectsPerOrganization(self, file_object):
    """Reads the projects per organization.

    Args:
      file_object (file): file-like object to read from.

    Returns:
      dict[str, list[str]]: organization names with corresponding project names.
    """
    # TODO: replace by:
    # config_parser = configparser. ConfigParser(interpolation=None)
    config_parser = configparser.RawConfigParser()
    config_parser.readfp(file_object)

    projects_per_organization = {}
    for option_name in config_parser.options(u'organizations'):
      project_names = self._GetConfigValue(
          config_parser, u'organizations', option_name)

      if project_names is None:
        project_names = []
      elif isinstance(project_names, basestring):
        project_names = project_names.split(u',')

      projects_per_organization[option_name] = project_names

    return projects_per_organization

  def ReadUsernames(self, file_object):
    """Reads the usernames.

    Args:
      file_object: the file-like object to read from.

    Returns:
      dict[str, str]: user names with corresponding email address.
    """
    # TODO: replace by:
    # config_parser = configparser. ConfigParser(interpolation=None)
    config_parser = configparser.RawConfigParser()
    config_parser.readfp(file_object)

    usernames = {}
    for option_name in config_parser.options(u'usernames'):
      email_address = self._GetConfigValue(
          config_parser, u'usernames', option_name)

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
          u'Unable to download URL: {0:s} with error: {1:s}'.format(
              download_url, exception))
      return None, None

    if url_object.code != 200:
      return None, None

    return url_object.read(), url_object.info()


class GithubContributionsHelper(DownloadHelper):
  """Class that defines a github contributions helper."""

  def _ListContributionsForProject(
      self, organization, project_name, output_writer):
    """Lists the contributions of a specific project.

    Args:
      organization (str): name of the organization.
      project_name (str): name of the project.
      output_writer (OutputWriter): output writer.
    """
    download_url = (
        u'https://api.github.com/repos/{0:s}/{1:s}/stats/contributors').format(
            organization, project_name)

    contributions_data, response = self._DownloadPageContent(download_url)
    if not contributions_data:
      return

    contributions_json = json.loads(contributions_data)
    self._WriteContribution(project_name, contributions_json, output_writer)

    # TODO: check if response is not None

  def _WriteContribution(self, project_name, contributions_json, output_writer):
    """Writes the contributions to the output writer.

    Args:
      project_name (str): name of the project.
      contributions_json (list[object]): JSON formatted contributions objects.
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

      # TODO: map login name to username

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

        output_line = (
            u'{0:s}\t{1:s}\t{2:s}\t{3:s}\t{4:d}\t{5:d}\t{6:d}\n').format(
                year, week_number, login_name, project_name,
                number_of_contributions, number_of_lines_added,
                number_of_lines_deleted)

        output_writer.Write(output_line.decode(u'utf-8'))

  def ListContributions(self, projects_per_organization, output_writer):
    """Lists the contributions of projects.

    Args:
      projects_per_organization (dict[str, list[str]]): organization names
          with corresponding projects names.
      output_writer (OutputWriter): output writer.
    """
    output_line = (
        u'year\tweek number\tlogin name\tproject\tnumber of contributions\t'
        u'number lines added\tnumber lines deleted\n')
    output_writer.Write(output_line.decode(u'utf-8'))

    for organization, projects in iter(projects_per_organization.items()):
      for project_name in projects:
        self._ListContributionsForProject(
            organization, project_name, output_writer)


class CodeReviewIssuesHelper(DownloadHelper):
  """Class that defines a Rietveld code review issues helper."""

  def _ListReviewsForEmailAddress(self, email_address, output_writer):
    """Lists the reviews of a specific email address.

    Args:
      email_address (str): email address of the reviewer.
      output_writer (OutputWriter): output writer.
    """
    issue_numbers = set()

    cursor = None
    while True:
      download_url = (
          u'https://codereview.appspot.com/search?reviewer={0:s}'
          u'&format=json&keys_only=False&with_messages=True').format(
              email_address)

      # TODO: for now only search open issues.
      # 1 => Unknown
      # 2 => Yes
      # 3 => No
      download_url = u'{0:s}&closed=3'.format(download_url)

      if cursor:
        download_url = u'{0:s}&cursor={1:s}'.format(download_url, cursor)

      reviews_data, response = self._DownloadPageContent(download_url)
      if not reviews_data:
        break

      # TODO: check if response is not None

      reviews_json = json.loads(reviews_data)

      for review_values in self._ParserReviewsJSON(reviews_json):
        if review_values[0] in issue_numbers:
          return

        issue_numbers.add(review_values[0])

        if review_values[2]:
          continue

      cursor = reviews_json.get(u'cursor', None)

  def _ParserReviewsJSON(self, reviews_json):
    """Parser the reviews JSON data.

    Args:
      reviews_json (dict[str, object]): JSON reviews object.

    Yield:
      tuple[str, str, str]: issue number, subject, is closed.
    """
    results_list_json = reviews_json.get(u'results', None)
    if results_list_json is None:
      logging.error(u'Missing results JSON list.')
      return

    for review_json in results_list_json:
      issue_number = review_json.get(u'issue', None)
      if issue_number is None:
        logging.error(u'Missing issue number.')
        continue

      subject = review_json.get(u'subject', None)
      if subject is None:
        logging.error(u'Missing subject.')
        continue

      is_closed = review_json.get(u'closed', False)

      yield issue_number, subject, is_closed

      reviewers_list_json = review_json.get(u'reviewers', None)
      if not reviewers_list_json:
        logging.error(u'Missing reviewers JSON list.')
        continue

      messages_list_json = review_json.get(u'messages', None)
      if not messages_list_json:
        logging.error(u'Missing messages JSON list.')
        continue

      for message_json in messages_list_json:
        sender_value = message_json.get(u'sender', None)
        if not sender_value:
          logging.error(u'Missing sender JSON value.')
          continue

    # TODO: based on the messages determine if the reviewer commented
    # on the CL.

    # "closed": false,
    # "issue": 294010043

    # TODO: map email address to username

    # TODO: get project from: "subject" e.g. "[plaso] ..."

  def ListIssues(self, usernames, output_writer):
    """Lists the code review issues of users.

    Args:
      usernames (dict[str, str]): usernames with corresponding email addresses
          of the reviewers.
      output_writer (OutputWriter): output writer.
    """
    # TODO: determine what to print as a header
    output_line = u'email address\t\n'
    output_writer.Write(output_line.decode(u'utf-8'))

    for email_address in iter(usernames.values()):
      self._ListReviewsForEmailAddress(email_address, output_writer)


class StdoutWriter(object):
  """Class that defines a stdout output writer."""

  def __init__(self):
    """Initializes an output writer object."""
    super(StdoutWriter, self).__init__()

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
      data (bytes): data to write.
    """
    print(data, end=u'')


def Main():
  """The main program function.

  Returns:
    bool: True if successful or False if not.
  """
  statistics_types = frozenset([
      u'codereviews', u'contributions'])

  argument_parser = argparse.ArgumentParser(description=(
      u'Generates an overview of project statistics of github projects.'))

  argument_parser.add_argument(
      u'-c', u'--config', dest=u'config_path', action=u'store',
      metavar=u'CONFIG_PATH', default=None, help=(
          u'path of the directory containing the statistics configuration '
          u'files e.g. stats.ini.'))

  argument_parser.add_argument(
      u'statistics_type', choices=sorted(statistics_types), action=u'store',
      metavar=u'TYPE', default=None, help=u'The statistics type.')

  options = argument_parser.parse_args()

  if not options.statistics_type:
    print(u'Statistics type missing.')
    print(u'')
    argument_parser.print_help()
    print(u'')
    return False

  config_path = options.config_path
  if not config_path:
    config_path = os.path.dirname(__file__)
    config_path = os.path.dirname(config_path)
    config_path = os.path.join(config_path, u'data')

  stats_file = os.path.join(config_path, u'stats.ini')
  if not os.path.exists(stats_file):
    print(u'No such config file: {0:s}.'.format(stats_file))
    print(u'')
    return False

  output_writer = StdoutWriter()

  if not output_writer.Open():
    print(u'Unable to open output writer.')
    print(u'')
    return False

  if options.statistics_type == u'codereviews':
    usernames = {}
    with open(stats_file) as file_object:
      stats_definition_reader = StatsDefinitionReader()
      usernames = stats_definition_reader.ReadUsernames(file_object)

    codereviews_helper = CodeReviewIssuesHelper()
    codereviews_helper.ListIssues(usernames, output_writer)

  elif options.statistics_type == u'contributions':
    projects_per_organization = {}
    with open(stats_file) as file_object:
      stats_definition_reader = StatsDefinitionReader()
      projects_per_organization = (
          stats_definition_reader.ReadProjectsPerOrganization(file_object))

    contributions_helper = GithubContributionsHelper()
    contributions_helper.ListContributions(
        projects_per_organization, output_writer)

  # TODO: add support for code reviews
  # TODO: add support for pull requests
  # TODO: add support for more granular CL information

  return True


if __name__ == '__main__':
  if not Main():
    sys.exit(1)
  else:
    sys.exit(0)
