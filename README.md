# Application with piCamera

## Feature
- Take Photo
- Start/Stop Record
- Stream via UDP
- Receive data control via TCP

## Increase swap memory cho raspi
```
	sudo swapon --show 
	free -h 
	sudo fallocate -l 4G /swapfile 
	sudo chmod 600 /swapfile 
	ls -lh /swapfile 
	sudo mkswap /swapfile 
	sudo swapon /swapfile 
	sudo cp /etc/fstab /etc/fstab.bak 
	echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```
 
## Install lib
```
  pip install opencv-python
  sudo apt install -y python3-pyqt5 python3-opengl
  
  sudo apt update && sudo apt upgrade
  
  sudo apt install -y python3-picamera2
  
  sudo apt install -y python3-libcamera python3-kms++
  sudo apt install -y python3-pyqt5 python3-prctl libatlas-base-dev ffmpeg python3-pip
  pip3 install numpy --upgrade
  pip3 install picamera2[gui]
  
  pip install pytz
```

Add command into ```/etc/pip.conf```: 
```
  sudo nano /etc/pip.conf
  break-system-packages = true
```
## Check USB Camera

Check /dev/video of usbcamera and replace it into code:
```
  sudo apt install v4l-utils
  v4l2-ctl --list-devices
```

## Create .service file

Create and open .service file: 
```
sudo nano /etc/systemd/system/picamera.service
```

`picamera.service` file
```
[Unit]
Description=Picamera
After=multi-user.target

[Service]
User=raspi
WorkingDirectory=/home/raspi/src
ExecStart=/usr/bin/python /home/raspi/src/test.py

[Install]
WantedBy=multi-user.target
```

Run service file and check status:
```
sudo systemctl start picamera.service
sudo systemctl enable picamera.service
sudo systemctl status picamera.service
```

