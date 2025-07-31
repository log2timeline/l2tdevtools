#!/bin/bash
#
# Script to build RPM packages with Docker.

# Fail on error.
set -e

GID=$(id -g);

L2TBUILDS_DIRECTORY="${HOME}/Projects/l2tbuilds";

cd config/docker;

mkdir -p "${L2TBUILDS_DIRECTORY}/rpm";
mkdir -p "${L2TBUILDS_DIRECTORY}/srpm";

# Build the l2tbuilds Fedora Docker image.
docker build -f l2tbuilds_fedora.Dockerfile --force-rm --no-cache -t log2timeline/l2tbuilds_fedora . ;
docker run -it -u ${UID}:${GID} -v "${L2TBUILDS_DIRECTORY}:/home/build/l2tbuilds:z" log2timeline/l2tbuilds_fedora /bin/bash

# docker run -u ${UID}:${GID} -v "${L2TBUILDS_DIRECTORY}:/home/build/l2tbuilds:z" log2timeline/l2tbuilds_fedora /bin/bash -c "(cd l2tdevtools && ./utils/build_dpkg.sh --preset plaso)"
