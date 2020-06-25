#!/usr/bin/env bash
#
# Script to install ${project_name} on Ubuntu from the GIFT PPA. Set the environment
# variable GIFT_PPA_TRACK if want to use a specific track. The default is dev.
#
# This file is generated by l2tdevtools update-dependencies.py any dependency
# related changes should be made in dependencies.ini.

# Exit on error.
set -e

GIFT_PPA_TRACK=$${GIFT_PPA_TRACK:-dev}

export DEBIAN_FRONTEND=noninteractive

# Dependencies for running ${project_name}, alphabetized, one per line.
# This should not include packages only required for testing or development.
${python_dependencies}

# Additional dependencies for running tests, alphabetized, one per line.
${test_dependencies}

# Additional dependencies for development, alphabetized, one per line.
${development_dependencies}

# Additional dependencies for debugging, alphabetized, one per line.
${debug_dependencies}

sudo add-apt-repository ppa:gift/$${GIFT_PPA_TRACK} -y
sudo apt-get update -q
sudo apt-get install -y $${PYTHON_DEPENDENCIES}

if [[ "$$*" =~ "include-debug" ]];
then
	sudo apt-get install -y $${DEBUG_DEPENDENCIES}
fi

if [[ "$$*" =~ "include-development" ]];
then
	sudo apt-get install -y $${DEVELOPMENT_DEPENDENCIES}
fi

if [[ "$$*" =~ "include-test" ]];
then
	sudo apt-get install -y $${TEST_DEPENDENCIES}
fi
