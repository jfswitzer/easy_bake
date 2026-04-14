#!/bin/bash
for hn in $(cat hostnames.txt); do
    ./stop_stress.sh $hn
done
