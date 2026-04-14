#!/bin/bash
for hn in $(cat hostnames.txt); do
    echo "############## $hn ##############"
    ssh baking@$hn.dynamic.ucsd.edu "top -bn 1 | head -n 12 | tail -n 6"
done
