#!/bin/bash
#
# Script to run tests on Travis-CI.

# Exit on error.
set -e;

if test "${TRAVIS_OS_NAME}" = "osx";
then
	PYTHONPATH=/Library/Python/2.7/site-packages/ /usr/bin/python ./run_tests.py;

elif test "${TRAVIS_OS_NAME}" = "linux";
then
	if test -n "${TOXENV}";
	then
		tox --sitepackages ${TOXENV};

	elif test "${TRAVIS_PYTHON_VERSION}" = "2.7";
	then
		coverage erase
		coverage run --source=dfdatetime --omit="*_test*,*__init__*,*test_lib*" ./run_tests.py
	else
		python ./run_tests.py
	fi
fi
