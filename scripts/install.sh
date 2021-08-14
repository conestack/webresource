#!/bin/bash

for dir in lib include bin share; do
    if [ -d "$dir" ]; then
        rm -r "$dir"
    fi
done

python3 -m venv .
./bin/pip install coverage
./bin/pip install -e .[docs]
