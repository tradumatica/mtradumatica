# MTradumàtica

## Minimum hardware recommendations
* Linux (Ubuntu 14.04 LTS)
* 4-core (8 thread) CPU or more
* 12 GB of RAM or more
* 5 GB or more of free hard disk space, as much as possible recommended to train large models (big translators, using over one million sentence pairs)

## Installation instructions for Ubuntu 14.04 LTS

6-step (+1) procedure, it could take 1-2h depending on hardware specifications:

0. Download mtradumatica

```bash
$ git clone https://github.com/tradumatica/mtradumatica.git
$ cd mtradumatica
```

1. Ensure that all prerequisites are installed
```bash
$ sudo ./scripts/run-as-root.sh
```
2. Download and install local dependencies
```bash
$ ./scripts/install.sh
```
3. Create the system database database 
```bash
$ source venv/bin/activate
$ python db_create.py
$ deactivate
```
4. Start service

```bash
$ ./scripts/startup.sh
```
5. Go to "http://localhost:8080" with a web browser
6. Enjoy!

## Troubleshooting

### Setting the service port

Before the startup, edit the file `conf/gunicorn.conf` and locat the following line 

```bash
bind         = '0.0.0.0:8080'
```
Here, replace 8080 by another port number (<= 65535).

