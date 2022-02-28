#!/bin/bash

./scripts/clean.sh

python3 -m venv .
./bin/pip install wheel coverage
./bin/pip install -e .[docs]
