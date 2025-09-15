sudo cp test_tryboot.txt /boot/firmware/tryboot.txt
sudo cp /home/baking/easy_bake/testing/stress/eb_stress.service /etc/systemd/system
sudo systemctl start eb_stress
sudo systemctl enable eb_stress
sudo reboot '0 tryboot'
