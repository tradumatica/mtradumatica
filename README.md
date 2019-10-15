# MTradumàtica on Python 3 🐍

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

Both installation procedures can provide multiple user accounts inside Mtradumatica based on the Google identity server through the OAUTH2 protocol. The procedure of setting such a server in the Google side is a bit complex and Google changes it from time to time, but it can be found [here]( https://developers.google.com/identity/protocols/OAuth2UserAgent). Although not official, a useful resource is [this video](https://www.youtube.com/watch?v=A_5zc3DYZfs).

From the process above, you will get at the end two strings, "client ID" and "client secret". You can edit the config.py file in the following way (alternatively, you can create a instance/config.py file with the following content):

```python
SECRET_KEY = 'put a random string here'
DEBUG      = False
ADMINS     = ['your.admin.account@gmail.com', 'your.second.admin.account@gmail.com']

USER_LOGIN_ENABLED          = True
OAUTHLIB_INSECURE_TRANSPORT = True # True also behind firewall,  False -> require HTTPS
GOOGLE_OAUTH_CLIENT_ID      = 'xxxxxxx-xxxxxxxxxxxxxxxxxxxxxxxxx.apps.googleusercontent.com'
GOOGLE_OAUTH_CLIENT_SECRET  = 'xxxxxxxxxxxxxxx'
```
The admin accounts in ADMINS will allow you to use admin features as translator optimization or the remote Moses server. You can set as many as you want.

## Add new languages to the interface

When you want to add a new language, follow the next procedure:

#### 1. Add the new language to the LANGUAGES item in config.py

You need a language code and the name of the language. The language code is
normally an [ISO-639-1 code](https://en.wikipedia.org/wiki/List_of_ISO_639-1_codes)
and the name should be the native language name for each code. For example,
if we want to add Portuguese we will change this

```python
LANGUAGES = { 'ca': u'Català', 'en': u'English', 'es': u'Spanish' }
```

for this

```python
LANGUAGES = { 'ca': u'Català', 'en': u'English', 'es': u'Spanish', 'pt': u'Português'}
```
Note the small u BEFORE and STICKED to the quotation marks after the colons.
Uncoment the line if necessary.

#### 2. Get the .po file for the new language

For the case of Portuguese, proceed in this way

```bash
$ source venv/bin/activate
(venv) $ cd app
(venv) $ pybabel extract -F babel.cfg -o messages.pot .
(venv) $ pybabel init -i messages.pot -d translations -l pt
```

Then you will find the file at `app/translations/pt/LC_MESSAGES/messages.po`
to translate it using your preferred tool or editor.

#### 3. Deploy the translations

Just restore the `messages.po` file to the very same path you found it and
execute:

```bash
$ source venv/bin/activate
(venv) $ cd app
(venv) $ pybabel compile -d translations
```

Then you can restart the system and look at the new translations

#### 4. Make the new translation available in the repository

```bash
$ git add app/translations/pt/LC_MESSAGES/messages.po
$ git commit -m "New interface language Portuguese"
$ git push
```

### Propagate source code modifications to the translations

Execute

```bash
$ source venv/bin/activate
(venv) $ cd app
(venv) $ pybabel extract -F babel.cfg -o messages.pot .
(venv) $ pybabel update -i messages.pot -d translations
(venv) $ pybabel compile -d translations
```

Then edit all .po files to translate the new strings

### Remove "fuzzy" marks

When you find a "fuzzy" comment after a hash inside the po files, check it
and remove this comment before compiling.
