#!/bin/bash

to_remove=(
    .coverage
    bin
    htmlcov
    include
    lib64
    lib
    local
    share
)

for item in "${to_remove[@]}"; do
    if [ -e "$item" ]; then
        rm -rf "$item"
    fi
done
