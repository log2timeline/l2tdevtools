#!/bin/bash
# A small script that runs the linter on all changed files.

EXIT_FAILURE=1;
EXIT_SUCCESS=0;

if ! test -f "utils/common.sh";
then
  echo "Missing common functions, are you in the wrong directory?";

  exit ${EXIT_FAILURE};
fi

. utils/common.sh

if ! linting_is_correct;
then
  echo "Aborted - fix the issues reported by the linter.";

  exit ${EXIT_FAILURE};
fi

exit ${EXIT_SUCCESS};

