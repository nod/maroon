#!/bin/bash
export PYTHONPATH=".."
cd tests
for t in basic file query
do
    echo "running $t"
    python $t"_tests.py"
done

echo "not running couch"
#python database_tests.py couch

echo "running mongo"
python database_tests.py mongo
