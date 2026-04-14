#!/bin/bash

mkdir -p coremark_outputs
for h in $(cat hostnames.txt); do
     echo $h
     mkdir -p coremark_outputs/$h
     scp -r baking@$h.dynamic.ucsd.edu:/home/baking/coremark/litmus* coremark_outputs/$h
 done
