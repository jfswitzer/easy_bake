#!/bin/bash
for hn in $(cat hostnames.txt); do
    ./start_heartbeat.sh $hn
done
