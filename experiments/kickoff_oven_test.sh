scp test_tryboot.txt baking@$1:/home/baking
scp kickoff_oven.sh baking@$1:/home/baking
ssh baking@$1 'bash -s < /home/baking/kickoff_oven.sh'
