#!/bin/bash

PYTHONPATH=. python3 ./tools/build.py --builds-directory ../l2tbuilds/srpm --downloads-directory ../l2tbuilds/downloads $* srpm
