#!/bin/bash
PYTHON=${PYTHON:-python}
for module in buf seq bitview hexdump fields stream; do
$PYTHON -m doctest rupy/$module.py $@
done
