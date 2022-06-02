#!/bin/bash

PIDS=`ps -C python3 -o pid=`

echo $PIDS

for pid in $PIDS
do
    echo $pid
    kill $pid
done
