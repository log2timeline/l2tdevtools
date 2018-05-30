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
    """Initializes a github helper.

    Args:
      organization (str): github organization name.
      project (str): github project name.
    """
    super(GitHubHelper, self).__init__()

    self._organization = organization
    self._project = project
    self._url_lib_helper = url_lib.URLLibHelper()

  def CreatePullRequest(self, access_token, origin, title, body):
    """Creates a pull request.

    Args:
      access_token (str): github access token.
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

    response_data = json.loads(response_data)

    pull_request_number = response_data.get('number')

    return pull_request_number


  def CreatePullRequestReview(
      self, pull_request_number, access_token, reviewers):
    """Requests a GitHub review of a pull request.

    Args:
      pull_request_number (int): GitHub issue number of the pull request.
      access_token (str): github access token.
      reviewers (list[str]): github usernames to assign as reviewers.

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
      username (str): github username of the fork.

    Returns:
      str: git repository URL or None.
    """
    return 'https://github.com/{0:s}/{1:s}.git'.format(username, self._project)

  def QueryUser(self, username):
    """Queries a github user.

    Args:
      username (str): github user name.

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
