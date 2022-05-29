#!/bin/bash

source venv/bin/activate

echo "How many brokers do you want to start?"
read broker_number

pids=()
for i in $( eval echo {1..$broker_number} )
do
  python3 broker_node.py &
  broker_pid=$!
  echo $broker_pid
  pids+=( $broker_pid )
done

#for i in pids
#do
#  echo $pid
#done
#python3 broker_node.py &
#python3 broker_node.py &
#python3 broker_node.py &