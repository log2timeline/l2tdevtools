#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Script to manage code reviews."""

from __future__ import print_function
from __future__ import unicode_literals

import argparse
import os
import sys

from l2tdevtools.review_helpers import review


def Main():
  """The main program function.

  Returns:
    bool: True if successful or False if not.
  """
  argument_parser = argparse.ArgumentParser(
      description='Script to manage code reviews.')

  # TODO: add option to directly pass code review issue number.

  # yapf: disable
  argument_parser.add_argument(
      '--project-path', '--project_path', '-p', dest='project_path',
      action='store', default=os.getcwd(), help=(
          'Path to the project being reviewed.'))

  argument_parser.add_argument(
      '--allfiles', '--all-files', '--all_files', dest='all_files',
      action='store_true', default=False, help=(
          'Apply command to all files, currently only affects the lint '
          'command.'))

  argument_parser.add_argument(
      '--diffbase', dest='diffbase', action='store', type=str,
      metavar='DIFFBASE', default='upstream/master', help=(
          'The diffbase the default is upstream/master. This options is used '
          'to indicate to what "base" the code changes are relative to and '
          'can be used to "chain" code reviews.'))

  argument_parser.add_argument(
      '--nobrowser', '--no-browser', '--no_browser', dest='no_browser',
      action='store_true', default=False, help=(
          'Disable the functionality to use the webbrowser to get the OAuth '
          'token should be disabled.'))

  argument_parser.add_argument(
      '--noconfirm', '--no-confirm', '--no_confirm', dest='no_confirm',
      action='store_true', default=False, help=(
          'Do not ask for confirmation apply defaults.\n'
          'WARNING: only use this when you are familiar with the defaults.'))

  argument_parser.add_argument(
      '--offline', dest='offline', action='store_true', default=False, help=(
          'The review script is running offline and any online check is '
          'skipped.'))

  help_message = 'Enable code style checking with yapf.'
  argument_parser.add_argument(
      '--enable-yapf', '--enable_yapf', dest='enable_yapf', action='store_true',
      default=False, help=help_message)

  commands_parser = argument_parser.add_subparsers(dest='command')

  close_command_parser = commands_parser.add_parser('close')

  # TODO: add this to help output.
  close_command_parser.add_argument(
      'branch', action='store', metavar='BRANCH', default=None,
      help='name of the corresponding feature branch.')

  commands_parser.add_parser('create')
  commands_parser.add_parser('create-pr')
  commands_parser.add_parser('create_pr')

  merge_command_parser = commands_parser.add_parser('merge')

  # TODO: add this to help output.
  merge_command_parser.add_argument(
      'codereview_issue_number', action='store',
      metavar='CODEREVIEW_ISSUE_NUMBER', default=None,
      help='the codereview issue number to be merged.')

  # TODO: add this to help output.
  merge_command_parser.add_argument(
      'github_origin', action='store',
      metavar='GITHUB_ORIGIN', default=None,
      help='the github origin to merged e.g. username:feature.')

  merge_edit_command_parser = commands_parser.add_parser('merge-edit')

  # TODO: add this to help output.
  merge_edit_command_parser.add_argument(
      'github_origin', action='store',
      metavar='GITHUB_ORIGIN', default=None,
      help='the github origin to merged e.g. username:feature.')

  merge_edit_command_parser = commands_parser.add_parser('merge_edit')

  # TODO: add this to help output.
  merge_edit_command_parser.add_argument(
      'github_origin', action='store',
      metavar='GITHUB_ORIGIN', default=None,
      help='the github origin to merged e.g. username:feature.')

  commands_parser.add_parser('lint')

  commands_parser.add_parser('lint-test')
  commands_parser.add_parser('lint_test')

  open_command_parser = commands_parser.add_parser('open')

  # TODO: add this to help output.
  open_command_parser.add_argument(
      'codereview_issue_number', action='store',
      metavar='CODEREVIEW_ISSUE_NUMBER', default=None,
      help='the codereview issue number to be opened.')

  # TODO: add this to help output.
  open_command_parser.add_argument(
      'branch', action='store', metavar='BRANCH', default=None,
      help='name of the corresponding feature branch.')
  # yapf: enable

  # TODO: add submit option?

  commands_parser.add_parser('test')

  # TODO: add dry-run option to run merge without commit.
  # useful to test pending CLs.

  commands_parser.add_parser('update')

  commands_parser.add_parser('update-authors')
  commands_parser.add_parser('update_authors')

  commands_parser.add_parser('update-version')
  commands_parser.add_parser('update_version')

  options = argument_parser.parse_args()

  codereview_issue_number = None
  feature_branch = None
  github_origin = None

  print_help_on_error = False
  if options.command in ('close', 'open'):
    feature_branch = getattr(options, 'branch', None)
    if not feature_branch:
      print('Feature branch value is missing.')
      print_help_on_error = True

      # Support "username:branch" notation.
      if ':' in feature_branch:
        _, _, feature_branch = feature_branch.rpartition(':')

  if options.command in ('merge', 'open'):
    codereview_issue_number = getattr(options, 'codereview_issue_number', None)
    if not codereview_issue_number:
      print('Codereview issue number value is missing.')
      print_help_on_error = True

  if options.command in ('merge', 'merge-edit', 'merge_edit'):
    github_origin = getattr(options, 'github_origin', None)
    if not github_origin:
      print('Github origin value is missing.')
      print_help_on_error = True

  # yapf: disable
  if options.offline and options.command not in (
      'lint', 'lint-test', 'lint_test', 'test'):
    print('Cannot run: {0:s} in offline mode.'.format(options.command))
    print_help_on_error = True
  # yapf: enable

  if print_help_on_error:
    print('')
    argument_parser.print_help()
    print('')
    return False

  home_path = os.path.expanduser('~')
  netrc_path = os.path.join(home_path, '.netrc')
  if not os.path.exists(netrc_path):
    print('{0:s} aborted - unable to find .netrc.'.format(
        options.command.title()))  # yapf: disable
    return False

  review_helper = review.ReviewHelper(
      options.command,
      options.project_path,
      github_origin,
      feature_branch,
      options.diffbase,
      all_files=options.all_files,
      no_browser=options.no_browser,
      no_confirm=options.no_confirm)

  if not review_helper.InitializeHelpers():
    return False

  if not review_helper.CheckLocalGitState():
    return False

  if not options.offline and not review_helper.CheckRemoteGitState():
    return False

  if options.command == 'merge':
    if not review_helper.PrepareMerge(codereview_issue_number):
      return False

  if options.command in ('merge', 'merge-edit', 'merge_edit'):
    if not review_helper.PullChangesFromFork():
      return False

  if options.command == 'update':
    if not review_helper.PrepareUpdate():
      return False

  if not review_helper.Lint():
    return False

  if options.enable_yapf:
    if not review_helper.CheckStyle():
      return False

  if not review_helper.Test():
    return False

  result = False
  if options.command == 'create':
    result = review_helper.Create()

  elif options.command in ('create-pr', 'create_pr'):
    result = review_helper.CreatePullRequest()

  elif options.command == 'close':
    result = review_helper.Close()

  elif options.command in ('lint', 'lint-test', 'lint_test', 'test'):
    result = True

  elif options.command == 'merge':
    result = review_helper.Merge(codereview_issue_number)

  elif options.command == 'open':
    result = review_helper.Open(codereview_issue_number)

  elif options.command == 'update':
    result = review_helper.Update()

  elif options.command in ('update-authors', 'update_authors'):
    result = review_helper.UpdateAuthors()

  elif options.command in ('update-version', 'update_version'):
    result = review_helper.UpdateVersion()

  return result


if __name__ == '__main__':
  if not Main():
    sys.exit(1)
  else:
    sys.exit(0)
