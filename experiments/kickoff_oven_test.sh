scp test_tryboot.txt baking@132.239.10.$1:/home/baking
scp kickoff_oven.sh baking@132.239.10.$1:/home/baking
ssh baking@132.239.10.$1 'bash -s < /home/baking/kickoff_oven.sh'
