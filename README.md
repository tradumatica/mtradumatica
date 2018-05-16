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



