# MTradumàtica

## Installation instructions for Ubuntu 14.04 LTS

6-step (+1) procedure:

0. Download mtradumatica

```bash
$ git clone https://github.com/tradumatica/mtradumatica.git
$ cd mtradumatica
```

1. Ensure that all prerrequisites are installed
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
$ source deactivate
```
4. Start service

```bash
$ ./scripts/startup.sh
```
5. Go to "http://localhost:8080" with a web browser
6. Enjoy!
