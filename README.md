# MTradumàtica

## Fast installation instructions for Ubuntu 16.04 LTS or Ubuntu 18.04 LTS

6-step procedure:

#### 0. Download Mtradumàtica

```bash
$ git clone --recurse-submodules https://github.com/tradumatica/mtradumatica
```


#### 1. Ensure that all prerrequisites are installed
 
```bash
$ sudo MTRADUMATICADIR/scripts/run-as-root.sh
```

#### 2. Download and install local dependencies
 
```bash
$ MTRADUMATICADIR/scripts/install.sh
```

#### 3. Start service

```bash
$ MTRADUMATICADIR/scripts/startup.sh
```

#### 5. Browse to "http://localhost:8080"

## Docker-based installation (for Linux, Windows or Mac)

You may need to install Docker, you can get it from here https://www.docker.com/community-edition

4-step procedure:

#### 0. Download Mtradumàtica

```bash
$ git clone --recurse-submodules https://github.com/tradumatica/mtradumatica
```

#### 1. Build the Docker image

```bash
$ cd mtradumatica
$ docker build -t mtradumatica .
```

#### 2. Excute the container

```bash
$ docker run -p 8080:8080 -p10000:10000 -d --name mtradumatica mtradumatica
```

#### 3. Browse to "http://localhost:8080"

## Multiple user account setup

Both installation procedures can provide multiple user accounts inside Mtradumatica based on the Google identity server. The procedure of setting such a server in the Google side is a bit complex and Google changes it from time to time, but it can be found [here]( https://developers.google.com/identity/protocols/OAuth2UserAgent). Although not official, a useful source is [this video](https://www.youtube.com/watch?v=A_5zc3DYZfs).

From the process above, you will get at the end two strings, "client ID" and "client secret". You can edit the config.py file in the following way

```python
SECRET_KEY = 'put a random string here'
DEBUG      = False
ADMINS     = ['your.admin.account@gmail.com', 'your.second.admin.account@gmail.com']

USER_LOGIN_ENABLED          = True
OAUTHLIB_INSECURE_TRANSPORT = True # True also behind firewall,  False -> require HTTPS
GOOGLE_OAUTH_CLIENT_ID      = 'xxxxxxx-xxxxxxxxxxxxxxxxxxxxxxxxx.apps.googleusercontent.com'
GOOGLE_OAUTH_CLIENT_SECRET  = 'xxxxxxxxxxxxxxx'
```
The admin accounts will allow you to use admin features as translator optimization or the remote Moses server.

```

