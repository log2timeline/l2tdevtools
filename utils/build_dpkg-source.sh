#!/bin/bash

PYTHONPATH=. ./tools/build.py --builds-directory ../l2tbuilds/dpkg-source --downloads-directory ../l2tbuilds/downloads $* dpkg-source
