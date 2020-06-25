#!/bin/bash

. scripts/utils.sh

SCRIPTPATH="$( cd "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"

version=$1

cd ${SCRIPTPATH}../src/

[[ -z "$version" ]] && die "Required parameter [version] is missing." || success "Making tar with version: $version"

mkdir -p "figgy/${version}/bin"

cp -R dist/__main__/* "figgy/${version}/bin/"

tar -czvf figgy.tar.gz "figgy/${version}/bin/"