#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Script to retrieve github project statistics."""

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


class DownloadHelper(object):
  """Class that defines a download helper."""

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


class GithubContributionsHelper(DownloadHelper):
  """Class that defines a github contributions helper."""

  def _ListContributionsForProject(
      self, organization, project_name, output_writer):
    """Lists the contributions of a specific project.

    Args:
      organization: a string containing the name of the organization.
      project_name: a string containing the name of the project.
      output_writer: an output writer object (instance of OutputWriter).
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
      project_name: a string containing the name of the project.
      contributions_json: a list of JSON formatted contributions objects.
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
      projects_per_organization: a dictionary containing the github
                                 organization name as a key and a list of
                                 projects names as the value.
      output_writer: an output writer object (instance of OutputWriter).
    """
    output_line = (
        u'year\tweek number\tlogin name\tproject\tnumber of contributions\t'
        u'number lines added\tnumber lines deleted\n')
    output_writer.Write(output_line.decode(u'utf-8'))

    for organization, projects in iter(projects_per_organization.items()):
      for project_name in projects:
        self._ListContributionsForProject(
            organization, project_name, output_writer)


class RietveldReviewsHleper(DownloadHelper):
  """Class that defines a rietveld reviews helper."""

  def _ListReviewsForEmailAddress(self, email_address, output_writer):
    """Lists the contributions of a specific project.

    Args:
      email_address: a string containing the email address of the reviewer.
      output_writer: an output writer object (instance of OutputWriter).
    """
    download_url = (
        u'https://codereview.appspot.com/search?reviewer={0:s}'
        u'&format=json&keys_only=False&with_messages=True').format(
            email_address)

    reviews_data, response = self._DownloadPageContent(download_url)
    if not reviews_data:
      return

    reviews_json = json.loads(reviews_data)
    self._WriteReviews(email_address, reviews_json, output_writer)

    # TODO: check if response is not None

  def _WriteReviews(self, email_address, reviews_json, output_writer):
    """Writes the reviews to the output writer.

    Args:
      email_address: a string containing the email address of the reviewer.
      reviews_json: a dictionary containing the JSON reviews object.
      output_writer: an output writer object (instance of OutputWriter).
    """
    reviews_list_json = reviews_json.get("reviews", None)
    if not reviews_list_json:
      logging.error(u'Missing reviews JSON list.')
      return

    for review_json in reviews_list_json:
      messages_list_json = review_json.get("reviews", None)
      if not messages_list_json:
        logging.error(u'Missing messages JSON list.')
        continue

      for message_json in messages_list_json:
        sender_value = message_json.get("sender", None)
        if not sender_value:
          logging.error(u'Missing sender JSON value.')
          continue

    # TODO: based on the messages determine if the reviewer commented
    # on the CL.

    # "closed": false,
    # "issue": 294010043

    # TODO: map email address to username

    # TODO: get project from: "subject" e.g. "[plaso] ..."

  def ListReviews(self, email_addresses, output_writer):
    """Lists the reviews of users.

    Args:
      email_addresses: a list of strings of email addresses of the reviewers.
      output_writer: an output writer object (instance of OutputWriter).
    """
    # TODO: determine what to print as a header
    output_line = u'email address\t\n'
    output_writer.Write(output_line.decode(u'utf-8'))

    for email_address in email_addresses:
      self._ListReviewsForEmailAddress(email_address, output_writer)



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
  statistics_types = frozenset([
      u'codereviews', u'contributions'])

  argument_parser = argparse.ArgumentParser(description=(
      u'Generates an overview of project statistics of github projects.'))

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

  output_writer = StdoutWriter()

  if not output_writer.Open():
    print(u'Unable to open output writer.')
    print(u'')
    return False

  projects_per_organization = {
      u'dfirlabs': [u'focalpoint'],
      u'google': [u'dotty', u'rekall', u'timesketch'],
      u'log2timeline': [
          u'dfdatetime', u'dfvfs', u'dfwinreg', u'l2tdevtools', u'plaso'],
  }

  if options.statistics_type == u'codereviews':
    codereviews_helper = CodeReviewIssuesHelper()
    codereviews_helper.ListCodeReviews(usernames, output_writer)

  elif options.statistics_type == u'contributions':
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
