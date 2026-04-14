#!/bin/bash
for hn in $(cat hostnames.txt); do
    #echo "############## $hn ##############"
    VOLTS=$(ssh baking@$hn.dynamic.ucsd.edu "vcgencmd measure_volts core")
    echo "${VOLTS:5:6}"
done
