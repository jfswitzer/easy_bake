scp man_test.sh baking@132.239.10.$1:/home/baking
ssh baking@132.239.10.$1 'bash -s < /home/baking/man_test.sh'


