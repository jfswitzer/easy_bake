sudo cp /home/baking/easy_bake/testing/heartbeat/eb_heartbeat.service /etc/systemd/system
sudo cp /home/baking/easy_bake/testing/heartbeat/eb_heartbeat.timer /etc/systemd/system
sudo systemctl start eb_heartbeat
sudo systemctl enable eb_heartbeat
sudo systemctl daemon-reload
