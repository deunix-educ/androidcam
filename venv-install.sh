#!/bin/bash
echo "Create a virtual environment in $(pwd)"
echo
echo "usage: $0 <path-to-requirements.txt> <env-name>"
echo
if [ "$1" == "" ]; then
   exit
fi
REQUIREMENTS="$1"
VENV="$2"

if [ "$VENV" == "" ]; then
    VENV=".venv"
fi
echo "Create $(pwd)/$VENV from the requirements: $REQUIREMENTS"
rm -rf $VENV

python3 -m venv $VENV

source $(pwd)/$VENV/bin/activate
echo "Activate virtual environment $VENV"
echo "PIP path: $(command -v pip)"

pip install -U pip wheel setuptools
pip install -r $REQUIREMENTS
echo
echo "End of creation:  $(pwd)/$VENV"


