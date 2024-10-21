# picamera2

## Install lib

```
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
## Feature
- Take Photo
- Start/Stop Record
- Stream via UDP
- Receive data via TCP
  
## Create .service file

Create and open .service file: 
```
nano /etc/systemd/system
```

```picamera.service``` file
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

```
sudo systemctl start picamera.service
sudo systemctl enable picamera.service
sudo systemctl status picamera.service
```

