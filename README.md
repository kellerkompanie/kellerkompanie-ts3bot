# kellerkompanie-ts3bot

This project is a automated bot for Teamspeak3 that connects the Kellerkompanie backend with Teamspeak.

## Installation

### Requirements

* Python 3.13 or higher

### Create ts3bot user

Create user with disabled-login

```
sudo adduser --disabled-login ts3bot
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
