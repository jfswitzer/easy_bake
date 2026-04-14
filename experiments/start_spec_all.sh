#!/bin/bash
for ip in $(cat new_hosts.txt); do
    ./start_spec.sh $ip
done
