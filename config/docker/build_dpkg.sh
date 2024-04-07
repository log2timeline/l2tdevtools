#!/bin/bash
#
# Script to build Debian packages with Docker.

# Fail on error.
set -e

GID=$(id -g);

L2TBUILDS_DIRECTORY="${HOME}/Projects/l2tbuilds";
GNUPG_DIRECTORY="${HOME}/Projects/l2tbuilds-gnupg";

cd config/docker;

mkdir -p "${L2TBUILDS_DIRECTORY}/dpkg";
mkdir -p "${L2TBUILDS_DIRECTORY}/dpkg-source";

# Build the l2tbuilds Ubuntu Docker image.
docker build -f l2tbuilds_ubuntu.Dockerfile --force-rm --no-cache -t log2timeline/l2tbuilds_ubuntu . ;

if test -d "${GNUPG_DIRECTORY}";
then
	# Run the container in interactive mode ("run -it") to use gpg-agent to sign the builds
	docker run -it -u ${UID}:${GID} -v "${GNUPG_DIRECTORY}:/home/ubuntu/.gnupg:z" -v "${L2TBUILDS_DIRECTORY}:/home/build/l2tbuilds:z" log2timeline/l2tbuilds_ubuntu
else
	docker run -u ${UID}:${GID} -v "${L2TBUILDS_DIRECTORY}:/home/build/l2tbuilds:z" log2timeline/l2tbuilds_ubuntu /bin/bash -c "(cd l2tdevtools && ./utils/build_dpkg.sh --preset plaso)"
fi

