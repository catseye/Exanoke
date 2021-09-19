#!/bin/sh

APPLIANCES=""
if command -v python2 > /dev/null 2>&1; then
    APPLIANCES="$APPLIANCES tests/appliances/exanoke.py2.md"
fi
if command -v python3 > /dev/null 2>&1; then
    APPLIANCES="$APPLIANCES tests/appliances/exanoke.py3.md"
fi

if [ "x$APPLIANCES" = "x" ]; then
    echo "No suitable Python versions found."
    exit 1
fi

falderal $APPLIANCES README.md
