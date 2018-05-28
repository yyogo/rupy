#!/bin/bash
for module in buf ranges bitview hexdump fields stream; do
python -m doctest rupy/$module.py $@
done
