# MTradumàtica

## Installation instructions for Ubuntu 16.04 LTS or Ubuntu 18.04 LTS

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

#### 5. Browse to "http://localhost:80"
