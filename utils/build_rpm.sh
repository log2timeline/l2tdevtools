#!/bin/bash

PYTHONPATH=. python3 ./tools/build.py --builds-directory ../l2tbuilds/rpm --downloads-directory ../l2tbuilds/downloads $* rpm
