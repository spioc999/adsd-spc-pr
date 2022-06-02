#!/bin/bash

source venv/bin/activate

echo "How many brokers do you want to start?"
read broker_number

start=65535
pids=()
for i in $( eval echo {1..$broker_number} )
do
  python3 broker.py -sp $(expr $start - $i) &
  broker_pid=$!
  echo $broker_pid
  pids+=( $broker_pid )
  sleep 1
done

#for i in pids
#do
#  echo $pid
#done
#python3 broker.py &
#python3 broker.py &
#python3 broker.py &