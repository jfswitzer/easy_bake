#!/bin/bash

for hn in $(cat pssh_hosts.txt); do
    echo $hn
    mkdir -p pulled_logs/$hn
    scp -r baking@$hn:/home/baking/easy_bake/testing/probe/logs pulled_logs/$hn
done
