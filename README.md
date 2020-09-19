# kellerkompanie-ts3bot
This project is a automated bot for Teamspeak3 that connects the kellerkompanie backend with Teamspeak.

## Murgeye's TS3 API as submodule
Murgeye's Teamspeak3 API (https://github.com/Murgeye/teamspeak3-python-api) was added as a submodule, after you clone the repository you need to initialize the submodule (a.k.a. actually downloading the files):
```
cd kellerkompanie-ts3bot
git submodule update --init
```

## Installation
Users wanting to install this should be familiar with basic concepts of Linux and Python.

### Requirements
* Linux distribution (tested with Ubuntu 16.04)
* Python 3.7 or higher (+packages: flask, werkzeug)

### Create ts3bot user
Create user with disabled-login
```
sudo adduser --disabled-login ts3bot
```

### Clone repository & copy scripts
Go to the home directory of the new user and clone this repository
```
sudo su - ts3bot
cd ~
git clone https://github.com/kellerkompanie/kellerkompanie-ts3bot.git
```

The upcoming steps assert a python virtual environment inside the cloned
repo. If not already present install the virtualenv tools:
```
sudo apt-get update
sudo apt-get install python3-venv
```
Switch to the freshly cloned repo and initialize a virtual environment:
```
cd /home/ts3bot/kellerkompanie-ts3bot
python3 -m venv venv
```
To install the requirements we switch to the virtual environment and
install the packages using pip:
```
source venv/bin/activate
pip install -r requirements.txt
```


### Create startscript
In order to start the interface we create a little runscript
```
sudo su - ts3bot
cd ~
nano start_bot.sh
```
Now put the following content inside and save/exit using ```CTRL+X``` 
followed by ```y``` and ```ENTER```
```
#!/usr/bin/env bash

cd /home/ts3bot/kellerkompanie-ts3bot
git pull
source venv/bin/activate
python keko_bot.py
```
Make the shell script executable:
```
chmod +x start_bot.sh
```
Now you can run the interface using
```
./start_bot.sh
```

### Configure
On initial startup the config file will be created, adjust it:
```
nano /home/ts3bot/kellerkompanie-ts3bot/keko_bot.json
```
Default config:
```
{
    "default_channel": "TechSupport / RapeDungeon",
    "host": "ts.kellerkompanie.com",
    "nickname": "Kellerkompanie Bot",
    "password": "password",
    "port": 10011,
    "server_id": 1,
    "user": "serverqueryusername"
}
```

Same goes for the database config:
```
nano /home/ts3bot/kellerkompanie-ts3bot/database_config.json
```
Default config:
```
{
    "db_host": "localhost",
    "db_name": "keko_teamspeak",
    "db_password": "password",
    "db_username": "keko_teamspeak"
}
```

### Declaring as service
To have automatic start on machine boot, we add the script as systemd 
service:
```
sudo nano /etc/systemd/system/ts3bot.service
```
Then we add the following content:
```
[Unit]
Description=ts3bot
After=network.target

[Service]
User=ts3bot
ExecStart=/home/ts3bot/start_bot.sh
WorkingDirectory=/home/ts3bot
StandardOutput=syslog
StandardError=syslog
SyslogIdentifier=ts3bot
Restart=always

[Install]
WantedBy=multi-user.target
```
To assure that the logfiles are created we will add our service to rsyslog:
```
nano /etc/rsyslog.d/ts3bot.conf
```
With the following content:
```
if $programname == 'ts3bot' then /var/log/ts3bot.log
& stop
```
Now we create the logfile and make it readable for syslog:
```
touch /var/log/ts3bot.log
chown syslog:adm /var/log/ts3bot.log
sudo systemctl restart rsyslog
```
Finally we enable the service and register it to run on boot:
```
sudo systemctl daemon-reload
sudo systemctl start ts3bot.service
sudo systemctl enable ts3bot.service
```
