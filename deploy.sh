#!/bin/bash

PACKAGE_NAME=$(cat setup.py | grep -o "name=['\"]\(\w\|-\|_\)*['\"]" | sed "s/name=['\"]\(.*\)['\"]/\1/")
PREFIX_PATH=/data/qa/ltbot/venv/pypi
PACKAGES_DIR=$PREFIX_PATH/packages
INDEX_URL=http://localhost:7001/simple/

pip uninstall --yes $PACKAGE_NAME
python setup.py sdist
rm -rf ./*.egg-info
cp dist/$PACKAGE_NAME* $PACKAGES_DIR
pip install --index-url=$INDEX_URL $PACKAGE_NAME
rm -rf ./dist
