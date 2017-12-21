# MTradumàtica

## Installation instructions for Ubuntu 16.04 LTS

6-step procedure:
1. Ensure that all prerrequisites are installed

```bash
$ sudo MTRADUMATICADIR/scripts/run-as-root.sh
```
2. Download and install local dependencies

```bash
$ MTRADUMATICADIR/scripts/install.sh
```
3. Create the system database database 

```bash
$ source MTRADUMATICADIR/venv/bin/activate
$ python MTRADUMATICADIR/db_create.py
$ deactivate
```

4. Start service

```bash
$ MTRADUMATICADIR/scripts/startup.sh
```

5. Go to "http://localhost:8081" with a web browser
6. Enjoy!
