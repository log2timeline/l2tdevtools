#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Script to manage code reviews."""

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
      '--noedit', '--no-edit', '--no_edit', dest='no_edit', action='store_true',
      default=False, help=(
          'Do not allow edits from maintainers on the pull request.\n'
          'Changing this can result in a more tedious code review.'))

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

  commands_parser.add_parser('create-pr')
  commands_parser.add_parser('create_pr')

  commands_parser.add_parser('lint')

  commands_parser.add_parser('lint-test')
  commands_parser.add_parser('lint_test')

  commands_parser.add_parser('test')

  options = argument_parser.parse_args()

  feature_branch = None
  github_origin = None

  print_help_on_error = False
  if options.command == 'close':
    feature_branch = getattr(options, 'branch', None)
    if not feature_branch:
      print('Feature branch value is missing.')
      print_help_on_error = True

    # Support "username:branch" notation.
    elif ':' in str(feature_branch):
      _, _, feature_branch = feature_branch.rpartition(':')

  if options.offline and options.command not in (
      'lint', 'lint-test', 'lint_test', 'test'):
    print('Cannot run: {0:s} in offline mode.'.format(options.command))
    print_help_on_error = True

  if print_help_on_error:
    print('')
    argument_parser.print_help()
    print('')
    return False

  home_path = os.path.expanduser('~')
  netrc_path = os.path.join(home_path, '.netrc')
  if not os.path.exists(netrc_path):
    print('{0:s} aborted - unable to find .netrc.'.format(
        options.command.title()))
    return False

  review_helper = review.ReviewHelper(
      options.command,
      options.project_path,
      github_origin,
      feature_branch,
      all_files=options.all_files,
      no_browser=options.no_browser,
      no_confirm=options.no_confirm,
      no_edit=options.no_edit)

  if not review_helper.InitializeHelpers():
    return False

  if not review_helper.CheckLocalGitState():
    return False

  if not options.offline and not review_helper.CheckRemoteGitState():
    return False

  if not review_helper.Lint():
    return False

  if options.enable_yapf:
    if not review_helper.CheckStyle():
      return False

  if not review_helper.Test():
    return False

  result = False
  if options.command in ('create-pr', 'create_pr'):
    result = review_helper.CreatePullRequest()

  elif options.command == 'close':
    result = review_helper.Close()

  elif options.command in ('lint', 'lint-test', 'lint_test', 'test'):
    result = True

  return result


if __name__ == '__main__':
  if not Main():
    sys.exit(1)
  else:
    sys.exit(0)
