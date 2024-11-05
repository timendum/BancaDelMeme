#!/bin/bash

VIRTUAL_ENV=.testenv

if [ ! -d $VIRTUAL_ENV ]; then
  # set up virtual environment
  uv venv $VIRTUAL_ENV
  if [ -f $VIRTUAL_ENV/bin/activate ]; then
    source $VIRTUAL_ENV/bin/activate
  else
    source $VIRTUAL_ENV/Scripts/activate
  fi

  # install deps
  uv pip install -r requirements.txt
  uv pip install coverage
else
  # just activate virtual environment
  if [ -f $VIRTUAL_ENV/bin/activate ]; then
    source $VIRTUAL_ENV/bin/activate
  else
    source $VIRTUAL_ENV/Scripts/activate
  fi
fi

# load envvars
export CONFIG=cfg_test.json

# run tests
uv run test/prepare.py
uv run python -m coverage run --branch --source=src -m unittest discover --start=test --pattern=*.py && \
  uv run python -m coverage report && \
  uv run python -m coverage html
