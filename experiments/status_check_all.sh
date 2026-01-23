#!/bin/bash
for $i in $(cat ips.txt); do
    ./status_check.sh $i
done
