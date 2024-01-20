# Script to set up tests on AppVeyor MacOS.

set -e

brew update -q
brew install -q ${brew_packages} || true

