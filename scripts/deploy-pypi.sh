#! /bin/sh

SCRIPTPATH="$( cd "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"

cd ${SCRIPTPATH}../src/

rm dist/* || echo "Dist already gone."

python setup.py sdist bdist_wheel

twine upload dist/* 
