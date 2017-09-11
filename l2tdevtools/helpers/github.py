# -*- coding: utf-8 -*-
"""Helper for interacting with GitHub."""

from __future__ import unicode_literals

import json
import logging

from l2tdevtools.helpers import url_lib
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

  def CreatePullRequest(
      self, access_token, codereview_issue_number, origin, description):
    """Creates a pull request.

    Args:
      access_token (str): github access token.
      codereview_issue_number (int|str): codereview issue number.
      origin (str): origin of the pull request, formatted as:
          "username:feature".
      description (str): description.

    Returns:
      bool: True if the pull request was created.
    """
    title = '{0!s}: {1:s}'.format(codereview_issue_number, description)
    body = (
        '[Code review: {0!s}: {1:s}]'
        '(https://codereview.appspot.com/{0!s}/)').format(
            codereview_issue_number, description)

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

    except errors.ConnectionError as exception:
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

    except errors.ConnectionError as exception:
      logging.warning('{0!s}'.format(exception))
      return

    if response_data:
      return json.loads(response_data)
