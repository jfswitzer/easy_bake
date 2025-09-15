cp tryboot_template.txt tryboot_scratch.txt
echo "over_voltage=$1" >> tryboot_scratch.txt
echo "over_voltage_min=$1" >> tryboot_scratch.txt

scp tryboot_scratch.txt baking@132.239.10.$2:/home/baking
scp change_undervolt_rpi.sh baking@132.239.10.$2:/home/baking
ssh baking@132.239.10.$2 'bash -s < /home/baking/change_undervolt_rpi.sh'


