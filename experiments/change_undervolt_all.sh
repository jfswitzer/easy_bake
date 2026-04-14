#!/bin/bash
for ip in $(cat hostnames.txt); do
    ./change_undervolt.sh $1 $ip
done
