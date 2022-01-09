#!/bin/bash

PYTHONPATH=. ./tools/build.py --builds-directory ../l2tbuilds/rpm/ --downloads-directory ../l2tbuilds/downloads $* rpm
