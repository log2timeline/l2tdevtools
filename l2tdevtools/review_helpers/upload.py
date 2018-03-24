# -*- coding: utf-8 -*-
"""Helper for interacting with the Codereview upload.py tool."""
from __future__ import print_function
from __future__ import unicode_literals

import json
import logging
import os
import sys

# pylint: disable=import-error,no-name-in-module,ungrouped-imports
if sys.version_info[0] < 3:
  import urllib2 as urllib_error
  import urllib as  urllib_parse
  import urllib2 as urllib_request
else:
  import urllib.error as urllib_error
  import urllib.parse as urllib_parse
  import urllib.request as urllib_request

# pylint: disable=wrong-import-position
from l2tdevtools.review_helpers import cli
from l2tdevtools.review_helpers import projects
from l2tdevtools.lib import upload as upload_tool


class UploadHelper(cli.CLIHelper):
  """Codereview upload.py command helper."""

  def __init__(self, email_address, no_browser=False):
    """Initializes a codereview helper.

    Args:
      email_address (str): email address.
      no_browser (Optional[bool]): True if the functionality to use the
          webbrowser to get the OAuth token should be disabled.
    """
    super(UploadHelper, self).__init__()
    self._access_token = None
    self._email_address = email_address
    self._no_browser = no_browser
    self._upload_py_path = os.path.join(
        os.path.dirname(__file__), '..', 'lib', 'upload.py')
    self._xsrf_token = None

  def AddMergeMessage(self, issue_number, message):
    """Adds a merge message to the code review issue.

    Where the merge is a commit to the main project git repository.

    Args:
      issue_number (int|str): codereview issue number.
      message (str): message to add to the code review issue.

    Returns:
      bool: merge message was added to the code review issue.
    """
    codereview_access_token = self.GetAccessToken()
    xsrf_token = self.GetXSRFToken()
    if not codereview_access_token or not xsrf_token:
      return False

    codereview_url = 'https://codereview.appspot.com/{0!s}/publish'.format(
        issue_number)

    post_data = urllib_parse.urlencode({
        'add_as_reviewer': 'False',
        'message': message,
        'message_only': 'True',
        'no_redirect': 'True',
        'send_mail': 'True',
        'xsrf_token': xsrf_token})

    request = urllib_request.Request(codereview_url)

    # Add header: Authorization: OAuth <codereview access token>
    request.add_header(
        'Authorization', 'OAuth {0:s}'.format(codereview_access_token))

    # This will change the request into a POST.
    request.add_data(post_data)

    try:
      url_object = urllib_request.urlopen(request)
    except urllib_error.HTTPError as exception:
      logging.error(
          'Failed publish to codereview issue: {0!s} with error: {1!s}'.format(
              issue_number, exception))
      return False

    if url_object.code not in (200, 201):
      logging.error((
          'Failed publish to codereview issue: {0!s} with status code: '
          '{1:d}').format(issue_number, url_object.code))
      return False

    return True

  def CloseIssue(self, issue_number):
    """Closes a code review issue.

    Args:
      issue_number (int|str): codereview issue number.

    Returns:
      bool: True if the code review was closed.
    """
    codereview_access_token = self.GetAccessToken()
    xsrf_token = self.GetXSRFToken()
    if not codereview_access_token or not xsrf_token:
      return False

    codereview_url = 'https://codereview.appspot.com/{0!s}/close'.format(
        issue_number)

    post_data = urllib_parse.urlencode({'xsrf_token': xsrf_token})

    request = urllib_request.Request(codereview_url)

    # Add header: Authorization: OAuth <codereview access token>
    request.add_header(
        'Authorization', 'OAuth {0:s}'.format(codereview_access_token))

    # This will change the request into a POST.
    request.add_data(post_data)

    try:
      url_object = urllib_request.urlopen(request)
    except urllib_error.HTTPError as exception:
      logging.error(
          'Failed closing codereview issue: {0!s} with error: {1!s}'.format(
              issue_number, exception))
      return False

    if url_object.code != 200:
      logging.error((
          'Failed closing codereview issue: {0!s} with status code: '
          '{1:d}').format(issue_number, url_object.code))
      return False

    return True

  def CreateIssue(self, project_name, diffbase, description):
    """Creates a new codereview issue.

    Args:
      project_name (str): name of the project.
      diffbase (str): diffbase.
      description (str): description.

    Returns:
      int: codereview issue number or None.
    """
    reviewer = projects.ProjectsHelper.GetReviewer(
        project_name, self._email_address)
    reviewers_cc = projects.ProjectsHelper.GetReviewersOnCC(
        project_name, self._email_address, reviewer)

    command = '{0:s} {1:s} --oauth2'.format(
        sys.executable, self._upload_py_path)

    if self._no_browser:
      command = '{0:s} --no_oauth2_webbrowser'.format(command)

    command = (
        '{0:s} --send_mail -r {1:s} --cc {2:s} -t "{3:s}" -y -- '
        '{4:s}').format(
            command, reviewer, reviewers_cc, description, diffbase)

    if self._no_browser:
      print(
          'Upload server: codereview.appspot.com (change with -s/--server)\n'
          'Go to the following link in your browser:\n'
          '\n'
          '    https://codereview.appspot.com/get-access-token\n'
          '\n'
          'and copy the access token.\n'
          '\n')
      print('Enter access token:', end=' ')

      sys.stdout.flush()

    exit_code, output, _ = self.RunCommand(command)
    print(output)

    if exit_code != 0:
      return

    issue_url_line_start = (
        'Issue created. URL: http://codereview.appspot.com/')
    for line in output.split(b'\n'):
      if issue_url_line_start in line:
        _, _, issue_number = line.rpartition(issue_url_line_start)
        try:
          return int(issue_number, 10)
        except ValueError:
          pass

  def GetAccessToken(self):
    """Retrieves the OAuth access token.

    Returns:
      str: codereview access token.
    """
    if not self._access_token:
      # TODO: add support to get access token directly from user.
      self._access_token = upload_tool.GetAccessToken()
      if not self._access_token:
        logging.error('Unable to retrieve access token.')

    return self._access_token

  def GetXSRFToken(self):
    """Retrieves the XSRF token.

    Returns:
      str: codereview XSRF token or None if the token could not be obtained.
    """
    if not self._xsrf_token:
      codereview_access_token = self.GetAccessToken()
      if not codereview_access_token:
        return

      codereview_url = 'https://codereview.appspot.com/xsrf_token'

      request = urllib_request.Request(codereview_url)

      # Add header: Authorization: OAuth <codereview access token>
      request.add_header(
          'Authorization', 'OAuth {0:s}'.format(codereview_access_token))
      request.add_header('X-Requesting-XSRF-Token', '1')

      try:
        url_object = urllib_request.urlopen(request)
      except urllib_error.HTTPError as exception:
        logging.error(
            'Failed retrieving codereview XSRF token with error: {0!s}'.format(
                exception))
        return

      if url_object.code != 200:
        logging.error((
            'Failed retrieving codereview XSRF token with status code: '
            '{0:d}').format(url_object.code))
        return

      self._xsrf_token = url_object.read()

    return self._xsrf_token

  def QueryIssue(self, issue_number):
    """Queries the information of a code review issue.

    The query returns JSON data that contains:
    {
      "description":str,
      "cc":[str],
      "reviewers":[str],
      "owner_email":str,
      "private":bool,
      "base_url":str,
      "owner":str,
      "subject":str,
      "created":str,
      "patchsets":[int],
      "modified":str,
      "project":str,
      "closed":bool,
      "issue":int
    }

    Where the "created" and "modified" strings are formatted as:
    "YYYY-MM-DD hh:mm:ss.######"

    Args:
      issue_number (int|str): codereview issue number.

    Returns:
      dict[str,object]: JSON response or None.
    """
    codereview_url = 'https://codereview.appspot.com/api/{0!s}'.format(
        issue_number)

    request = urllib_request.Request(codereview_url)

    try:
      url_object = urllib_request.urlopen(request)
    except urllib_error.HTTPError as exception:
      logging.error(
          'Failed querying codereview issue: {0!s} with error: {1!s}'.format(
              issue_number, exception))
      return

    if url_object.code != 200:
      logging.error((
          'Failed querying codereview issue: {0!s} with status code: '
          '{1:d}').format(issue_number, url_object.code))
      return

    response_data = url_object.read()
    response_data = response_data.decode('utf-8')
    return json.loads(response_data)

  def UpdateIssue(self, issue_number, diffbase, description):
    """Updates a code review issue.

    Args:
      issue_number (int|str): codereview issue number.
      diffbase (str): diffbase.
      description (str): description.

    Returns:
      bool: True if the code review was updated.
    """
    command = '{0:s} {1:s} --oauth2'.format(
        sys.executable, self._upload_py_path)

    if self._no_browser:
      command = '{0:s} --no_oauth2_webbrowser'.format(command)

    command = ('{0:s} -i {1!s} -m "Code updated." -t "{2:s}" -y -- '
               '{3:s}').format(command, issue_number, description, diffbase)

    if self._no_browser:
      print(
          'Upload server: codereview.appspot.com (change with -s/--server)\n'
          'Go to the following link in your browser:\n'
          '\n'
          '    https://codereview.appspot.com/get-access-token\n'
          '\n'
          'and copy the access token.\n'
          '\n')
      print('Enter access token:', end=' ')

      sys.stdout.flush()

    exit_code, output, _ = self.RunCommand(command)
    print(output)

    return exit_code == 0
