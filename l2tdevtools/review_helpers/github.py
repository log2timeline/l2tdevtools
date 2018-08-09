# -*- coding: utf-8 -*-
"""Helper for interacting with GitHub."""

from __future__ import unicode_literals

import json
import logging

from l2tdevtools.review_helpers import url_lib
from l2tdevtools.lib import errors


class GitHubHelper(object):
  """Github helper."""

  def __init__(self, organization, project):
    """Initializes a GitHub helper.

    Args:
      organization (str): GitHub organization name.
      project (str): GitHub project name.
    """
    super(GitHubHelper, self).__init__()

    self._organization = organization
    self._project = project
    self._url_lib_helper = url_lib.URLLibHelper()

  def AssignPullRequest(
      self, pull_request_number, access_token, assignees):
    """Adds assignees to a GitHub pull request.

    Assignees are responsible that a pull request is closed or merged.

    Args:
      pull_request_number (int): GitHub issue number of the pull request.
      access_token (str): GitHub access token.
      assignees (list[str]): GitHub usernames to assign.

    Returns:
      bool: True if the assignees were successfully added.
    """
    post_data = json.dumps({"assignees": assignees})

    github_url = (
        'https://api.github.com/repos/{0:s}/{1:s}/issues/{2:d}/'
        'assignees?access_token={3:s}').format(
            self._organization, self._project, pull_request_number,
            access_token)

    try:
      self._url_lib_helper.Request(github_url, post_data=post_data)

    except errors.ConnectivityError:
      return False

    return True

  def CreatePullRequest(self, access_token, origin, title, body):
    """Creates a pull request.

    Args:
      access_token (str): GitHub access token.
      origin (str): origin of the pull request, formatted as:
          "username:feature".
      title (str): title of the pull request.
      body (str): body of the pull request.

    Returns:
      int: GitHub issue number of the pull request.

    Raises:
      ConnectivityError: if there's an error communicating with GitHub.
    """
    post_data = (
        '{{\n'
        '  "title": "{0:s}",\n'
        '  "body": "{1:s}",\n'
        '  "head": "{2:s}",\n'
        '  "base": "master"\n'
        '}}\n').format(title, body, origin)

    github_url = (
        'https://api.github.com/repos/{0:s}/{1:s}/pulls?'
        'access_token={2:s}').format(
            self._organization, self._project, access_token)

    response_data = self._url_lib_helper.Request(
        github_url, post_data=post_data)

    if isinstance(response_data, bytes):
      response_data = response_data.decode('utf-8')

    response_data = json.loads(response_data)

    pull_request_number = response_data.get('number')

    return pull_request_number

  def CreatePullRequestReview(
      self, pull_request_number, access_token, reviewers):
    """Requests a GitHub review of a pull request.

    Args:
      pull_request_number (int): GitHub issue number of the pull request.
      access_token (str): GitHub access token.
      reviewers (list[str]): GitHub usernames to assign as reviewers.

    Returns:
      bool: True if the review was created.
    """
    post_data = json.dumps({"reviewers": reviewers})

    github_url = (
        'https://api.github.com/repos/{0:s}/{1:s}/pulls/{2:d}/'
        'requested_reviewers?access_token={3:s}').format(
            self._organization, self._project, pull_request_number,
            access_token)

    try:
      self._url_lib_helper.Request(github_url, post_data=post_data)

    except errors.ConnectivityError:
      return False

    return True

  def GetForkGitRepoUrl(self, username):
    """Retrieves the git repository URL of a fork.

    Args:
      username (str): GitHub username of the fork.

    Returns:
      str: git repository URL or None.
    """
    return 'https://github.com/{0:s}/{1:s}.git'.format(username, self._project)

  def GetUsername(self, access_token):
    """Retrieves a GitHub user.

    Args:
      access_token (str): GitHub access token.

    Returns:
      str: GitHub user name or None if not available.
    """
    github_url = (
        'https://api.github.com/user?access_token={0:s}').format(
            access_token)

    try:
      response_data = self._url_lib_helper.Request(github_url)
    except errors.ConnectivityError:
      return None

    if not response_data:
      return None

    response_data = json.loads(response_data)
    return response_data.get('login', None)

  def QueryUser(self, username):
    """Queries a GitHub user.

    Args:
      username (str): GitHub user name.

    Returns:
      dict[str,object]: JSON response or None if not available.
    """
    github_url = 'https://api.github.com/users/{0:s}'.format(username)

    try:
      response_data = self._url_lib_helper.Request(github_url)

    except errors.ConnectivityError as exception:
      logging.warning('{0!s}'.format(exception))
      return None

    if response_data:
      return json.loads(response_data)

    return None
