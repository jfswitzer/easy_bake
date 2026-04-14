#!/bin/bash

scp run_coremark.sh baking@$1:/home/baking/coremark
scp run_litmus.sh baking@$1:/home/baking/coremark
scp run_voltage.sh baking@$1:/home/baking/coremark
scp launch_litmus.sh baking@$1:/home/baking/coremark
ssh baking@$1 'bash -s < /home/baking/coremark/launch_litmus.sh'


