#!/bin/bash
#
# Script to set up Travis-CI test VM.

PYTHON2_DEPENDENCIES="pylint";

PYTHON2_TEST_DEPENDENCIES="python-coverage";

PYTHON3_DEPENDENCIES="";

PYTHON3_TEST_DEPENDENCIES="pylint";

# Exit on error.
set -e;

if test ${TRAVIS_OS_NAME} = "linux";
then
	if test ${TRAVIS_PYTHON_VERSION} = "2.7";
	then
		sudo apt-get install -y ${PYTHON2_DEPENDENCIES} ${PYTHON2_TEST_DEPENDENCIES};
	else
		sudo apt-get install -y ${PYTHON3_DEPENDENCIES} ${PYTHON3_TEST_DEPENDENCIES};
	fi
fi
