#!/bin/bash
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )" # get current directory
echo $DIR
source $DIR/venv/bin/activate
cd $DIR/src
python classify.py

