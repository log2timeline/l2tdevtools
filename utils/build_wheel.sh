#!/bin/bash

PYTHONPATH=. python3 ./tools/build.py --builds-directory ../l2tbuilds/wheel --downloads-directory ../l2tbuilds/downloads $* wheel
