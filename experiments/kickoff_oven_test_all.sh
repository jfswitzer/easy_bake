#!/bin/bash
for ip in $(cat ips.txt); do
    ./kickoff_oven_test.sh $ip
done
