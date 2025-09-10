#!/bin/bash

GPG_SESSION_FILE="/tmp/gpg-session-$$"

touch ${GPG_SESSION_FILE}

# Trigger GPG to unlock the passphrase for GPG agent.
gpg -q -d ${GPG_SESSION_FILE}

PYTHONPATH=. python3 ./tools/build.py --builds-directory ../l2tbuilds/dpkg-source --downloads-directory ../l2tbuilds/downloads $* dpkg-source

rm -f ${GPG_SESSION_FILE}
