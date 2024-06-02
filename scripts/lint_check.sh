# !/bin/bash

set -eux

pylint \
    --rcfile .static_analysis/.pylintrc \
    connect4 \
    tests

isort \
    --settings-file .static_analysis/.isort.cfg \
    .

black \
    --config .static_analysis/.black.cfg \
    .

# NOTE: Pyright expects a `pyrightconfig.json` to exist wherever the command is called from
pyright
