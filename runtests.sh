#!/bin/bash
cd tests
for test in *tests.py
do
	echo "running $test"
    python $test
done
