#!/bin/bash

scp cpu2017.tar.xz baking@132.239.10.$2:/home/baking
scp spec_script.sh baking@132.239.10.$2:/home/baking
ssh baking@132.239.10.$2 'bash -s < /home/baking/spec_script.sh'


