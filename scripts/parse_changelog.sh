#!/bin/sh

SCRIPTPATH="$( cd "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"

cd ${SCRIPTPATH}/../src

python setup.py install > /dev/null 2>&1

python ../scripts/parse_changelog.py