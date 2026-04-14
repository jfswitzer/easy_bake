#!/bin/bash

scp spec_script.sh baking@$1:/home/baking
scp spec_script_tmux.sh baking@$1:/home/baking
ssh baking@$1 'bash -s < /home/baking/spec_script.sh'


