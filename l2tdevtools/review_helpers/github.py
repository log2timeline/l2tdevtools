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
      bool: True if the pull request was created.
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

    try:
      self._url_lib_helper.Request(github_url, post_data=post_data)

    except errors.ConnectivityError as exception:
      # Handle existing PR HTTP status code 422.
      # Also see: https://github.com/log2timeline/l2tdevtools/issues/205
      logging.warning('{0!s}'.format(exception))
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
      dict[str,object]: JSON response or None.
    """
    github_url = 'https://api.github.com/users/{0:s}'.format(username)

    try:
      response_data = self._url_lib_helper.Request(github_url)

    except errors.ConnectivityError as exception:
      logging.warning('{0!s}'.format(exception))
      return

    if response_data:
      return json.loads(response_data)
