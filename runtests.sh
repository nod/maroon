#!/bin/bash
export PYTHONPATH=".."
cd tests
echo "running basic"
python basic_tests.py

echo "running couch"
python database_tests.py couch

echo "running mongo"
python database_tests.py mongo
