#!/bin/bash

./bin/python -m webresource.tests
./bin/coverage run --source webresource -m webresource.tests
./bin/coverage report
./bin/coverage html
