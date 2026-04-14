#!/bin/bash
for ip in $(cat hostnames.txt); do
    ./start_spec.sh $ip.dynamic.ucsd.edu
done
