#!/bin/bash
#
# Script to run tests on Travis-CI.

# Exit on error.
set -e;

if test "${TARGET}" = "pylint";
then
	pylint --version

	for FILE in `find l2tdevtools tests tools -name \*.py`;
	do
		echo "Checking: ${FILE}";

		pylint --rcfile=.pylintrc ${FILE};
	done

elif test "${TRAVIS_OS_NAME}" = "osx";
then
	PYTHONPATH=/Library/Python/2.7/site-packages/ /usr/bin/python ./run_tests.py;

elif test "${TRAVIS_OS_NAME}" = "linux";
then
	COVERAGE="/usr/bin/coverage";

	if ! test -x "${COVERAGE}";
	then
		# Ubuntu has renamed coverage.
		COVERAGE="/usr/bin/python-coverage";
	fi

	if test -n "${TOXENV}";
	then
		tox --sitepackages ${TOXENV};

	elif test "${TRAVIS_PYTHON_VERSION}" = "2.7";
	then
		${COVERAGE} erase
		${COVERAGE} run --source=dfdatetime --omit="*_test*,*__init__*,*test_lib*" ./run_tests.py
	else
		python ./run_tests.py
	fi
fi
