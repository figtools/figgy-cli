#!/bin/sh

python src/setup.py install > /dev/null 2>&1

python scripts/parse_changelog.py