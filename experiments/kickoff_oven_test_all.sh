#!/bin/bash
for hn in $(cat pssh_hosts.txt); do
    ./kickoff_oven_test.sh $hn
done
